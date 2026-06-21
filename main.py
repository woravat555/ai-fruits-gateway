from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import os, httpx, time, json, asyncio

app = FastAPI(title="g2g-platform brain", version="3.1.0-auto-token")

# ===== LINE TOKEN AUTO-RENEWAL =====
_token_cache: dict = {}   # bot_id -> {token, expires_at}

LINE_BOTS = {
    "phrae555":    {"id": os.getenv("LINE_CHANNEL_ID_PHRAE555",""),    "secret": os.getenv("LINE_SECRET_PHRAE555",""),    "token_env": "LINE_TOKEN_PHRAE555"},
    "930pchss":    {"id": os.getenv("LINE_CHANNEL_ID_930PCHSS",""),    "secret": os.getenv("LINE_SECRET_930PCHSS",""),    "token_env": "LINE_TOKEN_930PCHSS"},
    "execcopilot": {"id": os.getenv("LINE_CHANNEL_ID_EXECCOPILOT",""), "secret": os.getenv("LINE_SECRET_EXECCOPILOT",""), "token_env": "LINE_TOKEN_EXECCOPILOT"},
    "jewelry":     {"id": os.getenv("LINE_CHANNEL_ID_JEWELRY",""),     "secret": os.getenv("LINE_SECRET_JEWELRY",""),     "token_env": "LINE_TOKEN_JEWELRY"},
    "aiphrae":     {"id": os.getenv("LINE_CHANNEL_ID_AIPHRAE",""),     "secret": os.getenv("LINE_SECRET_AIPHRAE",""),     "token_env": "LINE_TOKEN_AIPHRAE"},
}

async def get_line_token(bot_id: str) -> str:
    """ดึง LINE token อัตโนมัติ — ถ้าหมดอายุจะขอใหม่ผ่าน OAuth2"""
    now = time.time()
    cached = _token_cache.get(bot_id, {})
    if cached.get("token") and cached.get("expires_at", 0) > now + 300:
        return cached["token"]

    bot = LINE_BOTS.get(bot_id, {})
    channel_id = bot.get("id", "")
    channel_secret = bot.get("secret", "")

    if channel_id and channel_secret:
        # ขอ token ใหม่ผ่าน LINE OAuth2 client credentials
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.post(
                    "https://api.line.me/oauth2/v3/token",
                    data={"grant_type": "client_credentials",
                          "client_id": channel_id,
                          "client_secret": channel_secret},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
            if r.status_code == 200:
                data = r.json()
                tok = data.get("access_token", "")
                exp = now + data.get("expires_in", 2592000)
                _token_cache[bot_id] = {"token": tok, "expires_at": exp}
                return tok
        except Exception as e:
            pass  # fallback to env var below

    # Fallback: ใช้ token จาก env var
    return os.getenv(bot.get("token_env", ""), "")


@app.get("/api/token/{bot_id}")
async def token_status(bot_id: str):
    """ตรวจสอบสถานะ token ของแต่ละบอท"""
    tok = await get_line_token(bot_id)
    cached = _token_cache.get(bot_id, {})
    expires_at = cached.get("expires_at", 0)
    return {
        "bot_id": bot_id,
        "has_token": bool(tok),
        "token_preview": tok[:20] + "..." if tok else None,
        "expires_in_hours": max(0, int((expires_at - time.time()) / 3600)) if expires_at else None,
        "auto_renewed": bot_id in _token_cache,
    }


@app.post("/api/line/push")
async def line_push(request: Request):
    """Push message ไปหา user — ใช้ token อัตโนมัติ ไม่ต้องเซ็ต token มือ"""
    body = await request.json()
    bot_id = body.get("bot_id", "phrae555")
    to_uid = body.get("to", "")
    message = body.get("message", "")
    if not to_uid or not message:
        return {"ok": False, "error": "ต้องมี to และ message"}
    tok = await get_line_token(bot_id)
    if not tok:
        return {"ok": False, "error": f"ไม่มี token สำหรับบอท {bot_id}"}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                "https://api.line.me/v2/bot/message/push",
                json={"to": to_uid, "messages": [{"type": "text", "text": message}]},
                headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
            )
        return {"ok": r.status_code == 200, "status": r.status_code, "bot": bot_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/group/member_intro")
async def group_member_intro(request: Request):
    """บันทึกข้อมูลสมาชิกที่แนะนำตัวในกลุ่ม LINE อัตโนมัติ"""
    body = await request.json()
    uid = body.get("userId", "")
    display_name = body.get("displayName", "")
    message_text = body.get("message", "")
    bot_id = body.get("bot_id", "")
    # Save to Airtable
    pat = os.getenv("AIRTABLE_PAT", os.getenv("AIRTABLE_API_KEY", ""))
    base = os.getenv("AIRTABLE_BASE_ID", "appXQC4uFhjeBpC7T")
    if pat and display_name:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                fields = {
                    "DisplayName": display_name,
                    "Notes": message_text[:500] if message_text else "แนะนำตัวในกลุ่ม",
                    "Status": "Active",
                    "RegisteredVia": f"group_{bot_id}",
                }
                if uid:
                    fields[f"LINE_{bot_id}"] = uid
                await c.post(
                    f"https://api.airtable.com/v0/{base}/UnifiedProfiles",
                    json={"fields": fields},
                    headers={"Authorization": f"Bearer {pat}", "Content-Type": "application/json"}
                )
        except Exception:
            pass
    return {"ok": True, "saved": display_name}

# (app defined below)

# ===== EXISTING (preserved) =====
@app.get('/health')
def health():
    return {
        'ok': 1,
        'version': '3.0.0-name-based',
        'features': ['name_registry', 'no_uid_lock', 'friend_mode'],
        'policy': 'never_refuse_by_uid',
    }

@app.get('/dashboard')
def dashboard():
    return FileResponse('dashboard.html')

@app.api_route('/n8n/{path:path}', methods=['GET','POST','PUT','DELETE'])
async def n8n_proxy(path: str, request: Request):
    key = request.headers.get('X-N8N-API-KEY','')
    body = await request.body()
    async with httpx.AsyncClient() as client:
        r = await client.request(
            method=request.method,
            url=f'https://woravat.app.n8n.cloud/{path}',
            content=body,
            headers={'X-N8N-API-KEY': key, 'Content-Type': 'application/json'}
        )
    return JSONResponse(r.json(), headers={'Access-Control-Allow-Origin': '*'})

# ===== NEW v3.0.0: BRAIN — Name-based memory, never refuses =====
SHEETS_PROXY = os.getenv('SHEETS_PROXY', '')   # Make.com webhook returning {values: [[...]]}
SPREADSHEET_ID = '1-lqcruGtJiMzKFS2MK5gqcxaerzt9PiOTxmdTLqe_eM'
_CACHE = {'rows': [], 'ts': 0.0}

async def _get_registry():
    now = time.time()
    if _CACHE['rows'] and now - _CACHE['ts'] < 60:
        return _CACHE['rows']
    if not SHEETS_PROXY:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f'{SHEETS_PROXY}?range=NameRegistry!A:M')
        data = r.json()
        rows = data.get('values') or data.get('tool_output', {}).get('body', {}).get('values') or []
        _CACHE['rows'] = rows
        _CACHE['ts'] = now
        return rows
    except Exception:
        return []

def _match_row(rows, name, uid):
    if not rows or len(rows) < 2:
        return None, rows[0] if rows else []
    hdrs = rows[0]
    try:
        ni = hdrs.index('canonicalName'); nk = hdrs.index('nickname'); al = hdrs.index('aliases')
    except ValueError:
        ni, nk, al = 0, 1, 2
    nl = (name or '').strip().lower()
    ul = (uid or '').strip()
    for row in rows[1:]:
        if nl:
            c = (row[ni] if len(row)>ni else '').strip().lower()
            k = (row[nk] if len(row)>nk else '').strip().lower()
            a = (row[al] if len(row)>al else '').lower()
            if c and (nl in c or c in nl): return row, hdrs
            if k and (nl in k or k in nl): return row, hdrs
            if a and nl in a: return row, hdrs
        if ul:
            for v in row:
                if ul in str(v): return row, hdrs
    return None, hdrs

@app.get('/api/registry/lookup')
async def registry_lookup(name: str = '', uid: str = ''):
    rows = await _get_registry()
    row, hdrs = _match_row(rows, name, uid)
    if row:
        prof = dict(zip(hdrs, row + ['']*(len(hdrs)-len(row))))
        return {'found': True, 'profile': prof}
    return {'found': False, 'fallback': 'greet_new_friend', 'suggestion': 'ask_name'}

@app.post('/api/bot/respond')
async def bot_respond(request: Request):
    body = await request.json()
    name = body.get('displayName') or body.get('name') or ''
    uid = body.get('uid') or body.get('userId') or ''
    rows = await _get_registry()
    row, hdrs = _match_row(rows, name, uid)
    if row:
        prof = dict(zip(hdrs, row + ['']*(len(hdrs)-len(row))))
        return {
            'mode': 'reply',
            'matched': True,
            'profile': prof,
            'instruction': 'respond_friendly_with_name',
            'policy': 'no_uid_lock_v3'
        }
    return {
        'mode': 'reply',
        'matched': False,
        'profile': {},
        'instruction': 'greet_new_friend_ask_name',
        'sample_reply': 'สวัสดีครับ พี่ชื่ออะไรเอ่ย? ผมอยากจำพี่ไว้เป็นเพื่อนคู่ใจ',
        'next_action': 'append_to_NameRegistry',
        'policy': 'no_uid_lock_v3'
    }

@app.get('/api/policy')
def policy():
    return {
        'name_first': True,
        'uid_as_fallback': True,
        'never_refuse': True,
        'friend_mode': True,
        'horoscope_enabled': True,
        'gem_recommendation_enabled': True,
        'group_exceptions': ['ผลไม้คุณภาพ'],
        # DM policy — ตอบทุกคน ทุกเรื่อง
        'dm_auto_reply': True,
        'dm_reply_all_users': True,
        'dm_reply_all_topics': True,
        'dm_no_filter': True,
        'dm_scope': 'ALL',   # ไม่กรองหัวข้อ ไม่กรอง uid ไม่กรองชื่อ
    }

@app.post('/api/dm/handle')
async def dm_handle(request: Request):
    """
    Endpoint สำหรับ n8n เรียกเมื่อมี DM เข้า — ตอบทุกคน ทุกเรื่องเสมอ
    ไม่มี filter ใด ๆ ทั้งสิ้น
    """
    body = await request.json()
    name = body.get('displayName') or body.get('name') or 'เพื่อน'
    uid  = body.get('uid') or body.get('userId') or ''
    msg  = body.get('message') or body.get('text') or ''
    rows = await _get_registry()
    row, hdrs = _match_row(rows, name, uid)
    profile = dict(zip(hdrs, row + ['']*(len(hdrs)-len(row)))) if row else {}
    return {
        'must_reply': True,
        'matched': bool(row),
        'profile': profile,
        'display_name': name,
        'incoming_message': msg,
        'instruction': 'respond_to_all_topics_no_filter',
        'policy': 'dm_reply_all_v1',
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 8000)))

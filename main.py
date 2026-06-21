from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import os, httpx, time

app = FastAPI(title="g2g-platform brain", version="3.0.0-name-based")

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

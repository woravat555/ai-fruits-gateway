"""
Platform Redundancy Patch v2.22.1+FarmerLink
Auto-loaded by Railway Gateway
Guidelines:
- P1: Railway (this server)
- P2: n8n fallback
- P3: Make.com repair alert ONLY - never primary
FarmerLink: Links LINE_UserID to FarmerRegistry (Airtable cols M=LINE_UserID N=LINE_DisplayName O=Linked_At)
"""
import os
import asyncio
import logging
from datetime import datetime
from fastapi import HTTPException, Request
import httpx

logger = logging.getLogger(__name__)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
MAKE_REPAIR_WEBHOOK = os.getenv("MAKE_REPAIR_WEBHOOK", "")
FARMER_LINK_WEBHOOK = os.getenv("FARMER_LINK_WEBHOOK", "")
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")
AIRTABLE_BASE = os.getenv("AIRTABLE_BASE_ID", "appXQC4uFhjeBpC7T")
FARMER_REGISTRY_TABLE = "tblrSHECLts3gs2P8"
_fail_counts = {"railway": 0, "n8n": 0}
_farmer_cache: dict = {}  # LINE_UserID -> farmer record cache (in-memory)


# --- FarmerLink: lookup LINE_UserID in Airtable FarmerRegistry ---------------

async def lookup_farmer_by_line_id(line_user_id: str):
    """Return farmer record from Airtable by LINE_UserID (col M). Cached in memory."""
    if line_user_id in _farmer_cache:
        return _farmer_cache[line_user_id]
    if not AIRTABLE_PAT:
        return None
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{FARMER_REGISTRY_TABLE}"
        params = {
            "filterByFormula": f'{{LINE_UserID}}="{line_user_id}"',
            "maxRecords": 1,
            "fields[]": ["ชื่อ-นามสกุล", "เบอร์โทรศัพท์", "LINE_UserID",
                          "LINE_DisplayName", "ชนิดพืช", "อำเภอ"]
        }
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(url, headers={"Authorization": f"Bearer {AIRTABLE_PAT}"}, params=params)
            if r.status_code == 200:
                records = r.json().get("records", [])
                if records:
                    farmer = records[0]["fields"]
                    farmer["_record_id"] = records[0]["id"]
                    _farmer_cache[line_user_id] = farmer
                    return farmer
    except Exception as e:
        logger.error(f"[FARMER-LINK] lookup error: {e}")
    return None


async def trigger_farmer_link_webhook(line_user_id: str, display_name: str = "", bot_id: str = "phrae555"):
    """Call FARMER_LINK_WEBHOOK to register/link LINE_UserID in FarmerRegistry."""
    if not FARMER_LINK_WEBHOOK:
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(FARMER_LINK_WEBHOOK, json={
                "line_user_id": line_user_id,
                "display_name": display_name,
                "bot_id": bot_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        logger.info(f"[FARMER-LINK] webhook triggered for {line_user_id[:8]}...")
    except Exception as e:
        logger.error(f"[FARMER-LINK] webhook error: {e}")


async def get_farmer_context(line_user_id: str, display_name: str = "", bot_id: str = "phrae555") -> dict:
    """Get farmer context for AI brain. Triggers link webhook if unknown user."""
    farmer = await lookup_farmer_by_line_id(line_user_id)
    if farmer:
        return {
            "known": True,
            "name": farmer.get("ชื่อ-นามสกุล", display_name),
            "phone": farmer.get("เบอร์โทรศัพท์", ""),
            "crops": farmer.get("ชนิดพืช", ""),
            "district": farmer.get("อำเภอ", ""),
            "record_id": farmer.get("_record_id", "")
        }
    # Unknown farmer -- trigger async link (non-blocking)
    asyncio.create_task(trigger_farmer_link_webhook(line_user_id, display_name, bot_id))
    return {"known": False, "name": display_name, "phone": "", "crops": "", "district": "", "record_id": ""}


# --- P2 / P3 handlers --------------------------------------------------------

async def forward_to_n8n_fallback(bot_id, user_id, message, reply_token=""):
    if not N8N_WEBHOOK_URL: return None
    try:
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.post(N8N_WEBHOOK_URL,
                headers={"Content-Type":"application/json","x-gateway-source":"railway-fallback"},
                json={"bot_id":bot_id,"user_id":user_id,"message":message,"reply_token":reply_token})
            if r.status_code == 200:
                _fail_counts["n8n"] = 0
                try: return r.json().get("response","")
                except: return r.text[:300] or None
    except Exception as e:
        _fail_counts["n8n"] += 1
        logger.error(f"[N8N-P2] {e}")
    return None


async def alert_make_repair_only(bot_id, detail):
    if not MAKE_REPAIR_WEBHOOK: return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.post(MAKE_REPAIR_WEBHOOK, json={
                "type":"ALL_PLATFORMS_FAILED","bot_id":bot_id,"detail":detail[:300]})
        logger.critical(f"[MAKE-P3-REPAIR] {bot_id}")
    except Exception as e: logger.error(f"[MAKE-P3-REPAIR] failed: {e}")


def _get_env_local():
    return {
        "phrae555":    {"token": os.getenv("LINE_TOKEN_PHRAD555","") or os.getenv("PHRAE555_CHANNEL_ACCESS_TOKEN","")},
        "930pchss":    {"token": os.getenv("LINE_TOKEN_930PCHSS","") or os.getenv("SALES_CHANNEL_ACCESS_TOKEN","")},
        "aiphrae":     {"token": os.getenv("LINE_TOKEN_AIPHRAE","") or os.getenv("AIPHRAE_CHANNEL_ACCESS_TOKEN","")},
        "jewelry":     {"token": os.getenv("LINE_TOKEN_JEWELRY","") or os.getenv("JEWELRY_CHANNEL_ACCESS_TOKEN","")},
        "execcopilot": {"token": os.getenv("LINE_TOKEN_EXECCOPILOT","") or os.getenv("EXEC_CHANNEL_ACCESS_TOKEN","")},
    }


def register_redundancy_routes(app, get_env_fn=None, secret=""):
    _secret = secret or os.getenv("DEPLOY_SECRET", "imperial-fruitia-2026")

    @app.post("/api/exec/broadcast")
    async def _broadcast(req: Request):
        b = await req.json()
        if b.get("secret") != _secret: raise HTTPException(403)
        env_fn = get_env_fn if callable(get_env_fn) else _get_env_local
        env = env_fn()
        res = {}
        sender = b.get("sender", "")
        msg = b.get("message","")
        async def _push(bid, tok):
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.post("https://api.line.me/v2/bot/message/broadcast",
                        headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"},
                        json={"messages":[{"type":"text","text":f"[{sender}->this bot]
{msg}"}]})
                    res[bid] = r.status_code
            except Exception as e: res[bid] = str(e)
        await asyncio.gather(*[_push(b,c.get("token","")) for b,c in env.items() if c.get("token")],
                             return_exceptions=True)
        return {"status":"broadcast","bots_reached":len(res),"results":res}

    @app.get("/api/platform/health")
    async def _platform_health():
        return {
            "p1": "Railway",
            "p2": f"n8n (config:{bool(N8N_WEBHOOK_URL)})",
            "p3": "Make.com repair-only",
            "farmer_link": f"configured:{bool(FARMER_LINK_WEBHOOK)}, cached:{len(_farmer_cache)}",
            "fails": _fail_counts
        }

    @app.post("/api/farmer/lookup")
    async def _farmer_lookup(req: Request):
        """Test endpoint: lookup farmer context by LINE_UserID."""
        b = await req.json()
        if b.get("secret") != _secret: raise HTTPException(403)
        uid = b.get("line_user_id", "")
        if not uid: raise HTTPException(400, "line_user_id required")
        ctx = await get_farmer_context(uid, b.get("display_name",""), b.get("bot_id","phrae555"))
        return ctx

    logger.info("[REDUNDANCY-PATCH] v2.22.1+FarmerLink registered")

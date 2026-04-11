"""
Platform Redundancy Patch v2.22.0
Auto-loaded by Railway Gateway
Guidelines:
- P1: Railway (this server)
- P2: n8n fallback
- P3: Make.com repair alert ONLY - never primary
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
_fail_counts = {"railway": 0, "n8n": 0}


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


def register_redundancy_routes(app, get_env_fn}, secret):
    """Call from main.py after app creation"""

    @app.post("/api/exec/broadcast")
    async def _broadcast(req: Request):
        b = await req.json()
        if b.get("secret") != secret: raise HTTPException(403)
        env = get_env_fn()
        res = {}
        sender = b.get("sender", "ท่าประหาร")
        msg = b.get("message","")
        async def _push(bid, tok):
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.post("https://api.line.me/v2/bot/message/broadcast",
                        headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"},
                        json={"messages":[{"type":"text","text":f"[{sender}->this bot]\n{msg}"}]})
                    res[bid] = r.status_code
            except Exception as e: res[bid] = str(e)
        await asyncio.gather(*[_push(b,c.get("token","")) for b,c in env.items() if c.get("token")],
                             return_exceptions=True)
        return {"status":"broadcast","bots_reached":len(res),"results":res}

    @app.get("/api/platform/health")
    async def _platform_health():
        return {"p1":"Railway","p2":f"n8n (config: {bool(N8N_WEBHOOK_URL)})","p3":"Make.com repair-only","fails":_fail_counts}

    logger.info("[REDUNDATCY-PATCH] v2.22.0 registered")

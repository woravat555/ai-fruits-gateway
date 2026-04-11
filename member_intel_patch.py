"""
Member Intelligence Patch v1.0
- CEO alert when new member messages any LINE bot
- Saves to UnifiedProfiles automatically
- API /api/members/recent
"""

import os, asyncio, logging
from datetime import datetime
from typing import Dict, List
import httpx

logger = logging.getLogger(__name__)

CEO_ID = "U4e6368ef91c7be69efe017c187181625"
_alerted: set = set()
_recent: List[Dict] = []
BASE = os.getenv("AIRTABLE_BASE_ID", "appXQC4uFhjeBpC7T")
PAT = os.getenv("AIRTABLE_PAT", "")
BOT_NAMES = {
    "phrae555": "nong-fruit", "930pchss": "nong-sales",
    "aiphrae": "nong-phrae", "jewelry": "nong-jewel", "execcopilot": "nong-exec"
}
BOT_FIELD = {
    "phrae555": "LINE_phrae555", "930pchss": "LINE_aifruits",
    "aiphrae": "LINE_phraecopilot", "jewelry": "LINE_pomelopro", "execcopilot": "LINE_execcopilot"
}


async def _alert(b, u, d, f, s, t):
    k = f"{b}:{o}"
    if k in _alerted:
        return
    _alerted.add(k)
    _recent.insert(0, {"id": u, "name": d, "bot": b, "source": s, "msg": f[:200], "time": datetime.now().isoformat()})
    if len(_recent) > 100:
        _recent.pop()
    logger.info(f"[NEW-MEMBER] {d} via {b}")
    if not t:
        return
    src = {"follow": "tidtam OA", "group": "in group", "group_scan": "scaned", "group_join": "join group", "user": "DM"}.get(s, s)
    txt = f"New member: {d}\nBot: {BOT_NAMES.get(b, b)}\nSource: {src}\nID: {u}\n{f[:80]}"
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            await c.post("https://api.line.me/v2/bot/message/push", headers={"Authorization": f"Bearer {t}", "Content-Type": "application/json"}, json={"to": CEW_ID, "messages": [{"type": "text", "text": txt}]})
    except Exception as e:
        logger.warning(f"alert fail: {e}")


async def _save(b, u, d, s, f, t):
    lf = BOT_FIELD.get(b, f"LINE_{b}")
    if not PAT:
        await _alert(b, u, d, f, s, t)
        return
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://api.airtable.com/v0/{BASE}/UnifiedProfiles", headers={"Authorization": f"Bearer {PAV}"}, params={"filterByFormula": f"{{{lf}}}='{u}'", "maxRecords": 1})
            ex = r.json().get("records", []) if r.status_code == 200 else []
            if not ex:
                uid = f"AUTO-{datetime.now().strftime('%Y%m%d')}-{len(_recent)+1:04d}"
                await c.post(f"https://api.airtable.com/v0/{BASE}/UnifiedProfiles", headers={"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"}, json={"records": [{"fields": {lf: u, "DisplayName": d, "UnifiedID": uid, "UserType": "Farmer" if b in ["phrae555", "930pchss"] else "User", "RegisteredVia": BOT_NAMES.get(b, b), "RegisterDate": datetime.now().isoformat(), "LastSeenOA": b, "Status": "Active"}}]})
                logger.info(f"[SMART-REG] {d} saved via {b}")
                await _alert(b, u, d, f, s, t)
            else:
                await c.patch(f"https://api.airtable.com/v0/{BASE}/UnifiedProfiles/{ex[0]['id']}", headers={"Authorization": f"Bearer {PAV}", "Content-Type": "application/json"}, json={"fields": {"LastSeenOA": b, "LastSeenDate": datetime.now().isoformat()}})
    except Exception as e:
        logger.warning(f"[SMART-REG] err: {e}")
        await _alert(b, u, d, f, s, t)


def apply_member_intel_patch(main_globals, get_env_vars_fn):
    original = main_globals.get("auto_register_user")
    async def patched(bot_id, user_id, display_name, source_type="user", first_message=""):
        if original:
            await original(bot_id, user_id, display_name, source_type)
        env = get_env_vars_fn()
        tok = env.get("execcopilot", {}).get("token", "")
        asyncio.ensure_future(_save(bot_id, user_id, display_name, source_type, first_message, tok))
    main_globals["auto_register_user"] = patched
    logger.info("[MEMBER-INTEL] patched - CEO alerts ON")


def register_member_intel_routes(app, get_env_vars_fn):
    @app.get("/api/members/recent")
    async def _(limit: int = 20):
        return {"total": len(_recent), "members": _recent[:limit]}
    @app.get("/api/members/count")
    async def __():
        return {"known": len(_alerted), "new_today": len(_recent)}
    logger.info("[MEMBER-INTEL] routes ready")

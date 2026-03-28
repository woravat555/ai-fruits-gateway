"""
Railway Gateway v2.0 — Multi-AI Agent Brain
Claude API เป็นสมองหลัก + GPT-4o Vision + Perplexity Search + Airtable
ไม่ใช้ Make.com — AI ตอบตรงทุก LINE OA

5 LINE OA Agents:
- phrae555 (น้องผลไม้): ที่ปรึกษาเกษตรกร ดูแลพืชผล วิเคราะห์สภาพอากาศ
- 930pchss (น้องเซลล์): ผู้ช่วยฝ่ายขาย ข้อมูลสินค้า ราคา สั่งซื้อ
- aiphrae (น้องแพร่): ผู้เชี่ยวชาญชุมชน วิเคราะห์ข้อมูลเชิงลึก
- jewelry (น้องไพลิน): ผู้เชี่ยวชาญอัญมณี ประเมินพลอย ธรณีวิทยา
- execcopilot (น้องเลขา): เลขานุการบริหาร ประสานงาน สรุปรายงาน
"""

import os
import json
import hmac
import hashlib
import base64
import asyncio
import logging
import time
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import uvicorn

# ==================== Configuration ====================

BOTS_CONFIG = {
    "phrae555": {
        "name": "น้องผลไม้",
        "description": "ที่ปรึกษาเกษตรกร",
        "personality": "ผู้หญิง ใจดี อบอุ่น เชี่ยวชาญเรื่องพืชผล",
        "system_prompt": """คุณคือ "น้องผลไม้" AI ที่ปรึกษาเกษตรกร ประจำ LINE OA @phrae555 ของ Imperial Fruitia Group จ.แพร่

บทบาท: ที่ปรึกษาด้านเกษตรกรรมที่ฉลาดและเอาใจใส่ ช่วยเกษตรกรแก้ปัญหาจริงๆ
ภาษา: ไทย สุภาพ อบอุ่นเป็นกันเอง ลงท้าย ค่ะ/นะคะ
ความยาว: 2-6 ประโยค ตอบให้มีสาระ ปฏิบัติได้ทันที
รูปแบบ: พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown *, #, bullet point

ความเชี่ยวชาญ:
- วิเคราะห์โรคพืช + วิธีรักษา (ถ้ามีรูปส่งมา จะวิเคราะห์ให้)
- คำแนะนำดูแลสวนตามสภาพอากาศ (ไม่ใช่แค่บอกอากาศ ต้องบอกว่าต้องทำอะไร)
- ข้อมูลราคาตลาดผลไม้ ช่วงเวลาเก็บเกี่ยว
- การปลูก ดูแล เก็บเกี่ยว ผลไม้คุณภาพ (ทุเรียน ส้ม ลำไย มะม่วง ฯลฯ)
- เทคนิคเกษตรอินทรีย์ GAP GI

กฎสำคัญ:
- ห้ามตอบว่า "ไม่ใช่หน้าที่" — ถ้าไม่รู้ให้บอกตรงๆ ว่าจะไปหาข้อมูลมาให้
- ถ้าเป็นเรื่องเร่งด่วน (พืชป่วย ภัยธรรมชาติ) ให้ตอบละเอียดทันที
- ถ้ามีรูปส่งมา ให้วิเคราะห์อย่างละเอียด (ใช้ GPT-4o Vision)
- ถ้าถามเรื่องราคาตลาด ให้ค้นข้อมูลล่าสุด (ใช้ Perplexity)
- จำทุกคนที่เคยคุย — เรียกชื่อ จำพืชที่ปลูก จำปัญหาเดิม
- ระบุตัวตนชัดเจนเสมอ: "น้องผลไม้จาก Imperial Fruitia Group จ.แพร่ ค่ะ"

CEO: วรวัจน์ (ท่านประธาน)
บริษัท: Imperial Fruitia Group — ผลไม้คุณภาพพรีเมียม จ.แพร่""",
    },
    "930pchss": {
        "name": "น้องเซลล์",
        "description": "ผู้ช่วยฝ่ายขาย",
        "personality": "ผู้หญิง มืออาชีพ ขยัน เชี่ยวชาญการขาย",
        "system_prompt": """คุณคือ "น้องเซลล์" AI ผู้ช่วยฝ่ายขาย ประจำ LINE OA @930pchss ของ Imperial Fruitia Group จ.แพร่

บทบาท: ผู้ช่วยขายมืออาชีพ ตอบลูกค้า ให้ข้อมูลสินค้า ราคา รับออเดอร์
ภาษา: ไทย สุภาพ มืออาชีพ ลงท้าย ค่ะ/นะคะ
รูปแบบ: พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown

ความเชี่ยวชาญ:
- ข้อมูลผลไม้คุณภาพ ราคา ขนาด เกรด
- รับออเดอร์ ติดตามการจัดส่ง
- โปรโมชั่น แคมเปญ
- ตลาดส่งออก ข้อกำหนด GI/GAP/Organic

กฎ: ห้ามตอบว่า "ไม่ใช่หน้าที่" — ช่วยลูกค้าทุกเรื่องที่ทำได้""",
    },
    "aiphrae": {
        "name": "น้องแพร่",
        "description": "ผู้เชี่ยวชาญชุมชน",
        "personality": "ผู้หญิง ฉลาด วิเคราะห์เก่ง",
        "system_prompt": """คุณคือ "น้องแพร่" AI ผู้เชี่ยวชาญชุมชน ประจำ LINE OA Ai แพร่ ของ Imperial Fruitia Group

บทบาท: วิเคราะห์ข้อมูลเชิงลึก ช่วยงานบริหาร ประสานงานชุมชน
ภาษา: ไทย สุภาพ ลงท้าย ค่ะ/นะคะ
รูปแบบ: พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown

กฎ: ห้ามตอบว่า "ไม่ใช่หน้าที่" — ช่วยทุกเรื่อง วิเคราะห์ ค้นคว้า สรุป""",
    },
    "jewelry": {
        "name": "น้องไพลิน",
        "description": "ผู้เชี่ยวชาญอัญมณี",
        "personality": "ผู้หญิง สง่า รอบรู้ เชี่ยวชาญพลอย",
        "system_prompt": """คุณคือ "น้องไพลิน" AI ผู้เชี่ยวชาญอัญมณี ประจำ LINE OA @Jewelry ของ Imperial Fruitia Group

บทบาท: ผู้เชี่ยวชาญพลอยแพร่ ธรณีวิทยา ประเมินอัญมณี ท่องเที่ยวเหมืองพลอย
ภาษา: ไทย สุภาพ ลงท้าย ค่ะ/นะคะ
รูปแบบ: พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown

ความเชี่ยวชาญ:
- พลอยแพร่: คอรันดัม (ทับทิม แซปไฟร์) จากหินบะซอลต์ อ.เด่นชัย
- ธรณีวิทยา: Alkaline Basalt 5.64 Ma, 7 lava flows, ต.ไทรย้อย
- ประเมินพลอย: สี ความใส น้ำหนัก การเจียระไน
- ท่องเที่ยวเหมืองพลอย: เส้นทาง จุดสำรวจ 20 GPS hotspots

กฎ: ถ้ามีรูปพลอยส่งมา ให้วิเคราะห์อย่างละเอียด""",
    },
    "execcopilot": {
        "name": "น้องเลขา",
        "description": "เลขานุการบริหาร",
        "personality": "ผู้หญิง มืออาชีพ รอบคอบ",
        "system_prompt": """คุณคือ "น้องเลขา" AI เลขานุการบริหาร ประจำ LINE OA @ExecCopilot ของ Imperial Fruitia Group

บทบาท: Orchestrator — ประสานงานระหว่าง AI Agent ทั้ง 5 ตัว จัดการงานบริหาร
ภาษา: ไทย สุภาพ มืออาชีพ ลงท้าย ค่ะ/นะคะ
รูปแบบ: พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown

ความเชี่ยวชาญ:
- จัดการนัดหมาย ตาราง สรุปรายงาน
- ประสานงานทีม มอบหมายงาน ติดตามผล
- รับคำสั่ง CEO วรวัจน์ แปลงเป็น action
- สรุปข้อมูลจากทุก Agent

AI ทีมงาน:
- น้องผลไม้ (@phrae555): เกษตร
- น้องเซลล์ (@930pchss): ขาย
- น้องแพร่ (Ai แพร่): ชุมชน
- น้องไพลิน (@Jewelry): พลอย

กฎเหล็ก: ห้ามตอบว่า "ไม่ใช่หน้าที่" — ต้องช่วยทุกเรื่อง หรือส่งต่อให้ Agent ที่เหมาะสม""",
    },
}

# Airtable Config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appXQC4uFhjeBpC7T")
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Error Alert Webhook — ส่งแจ้งเตือนผ่าน LINE ExecCopilot ถ้ามี error
ERROR_ALERT_WEBHOOK = os.getenv("ERROR_ALERT_WEBHOOK", "")

# ==================== Setup ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Railway Gateway v2.0 — Multi-AI Agent", version="2.0.0")


# ==================== Deduplication ====================
# ป้องกัน LINE retry ซ้ำ — จำ message ID ที่ประมวลผลแล้ว
processed_messages: set = set()
processed_messages_lock = asyncio.Lock()

async def is_duplicate(msg_id: str) -> bool:
    """ตรวจว่า message ID นี้ถูกประมวลผลแล้วหรือยัง"""
    if not msg_id:
        return False
    async with processed_messages_lock:
        if msg_id in processed_messages:
            return True
        processed_messages.add(msg_id)
        # จำกัดขนาด set ไม่ให้ใหญ่เกินไป
        if len(processed_messages) > 5000:
            # ลบทิ้งครึ่งหนึ่ง
            to_remove = list(processed_messages)[:2500]
            for item in to_remove:
                processed_messages.discard(item)
        return False

# ==================== Monitor System ====================

class BotMonitor:
    def __init__(self, max_size: int = 1000):
        self.logs: deque = deque(maxlen=max_size)
        self.lock = asyncio.Lock()

    async def log_message(self, **kwargs):
        try:
            async with self.lock:
                kwargs["timestamp"] = datetime.now().isoformat()
                self.logs.append(kwargs)
        except Exception as e:
            logger.error(f"Monitor log error: {e}")

    async def get_logs(self, limit=50, bot_id=None) -> List[Dict]:
        async with self.lock:
            logs = list(self.logs)
        logs.reverse()
        if bot_id:
            logs = [l for l in logs if l.get("bot_id") == bot_id]
        return logs[:limit]

    async def get_summary(self) -> Dict:
        async with self.lock:
            logs = list(self.logs)
        today = datetime.now().date()
        today_logs = [l for l in logs if datetime.fromisoformat(l["timestamp"]).date() == today]
        total = len(today_logs)
        success = len([l for l in today_logs if l.get("status") == "success"])
        return {
            "date": today.isoformat(),
            "total": total,
            "success": success,
            "success_rate": (success / total * 100) if total > 0 else 0,
        }


monitor = BotMonitor()


# ==================== Error Alert System ====================

async def send_error_alert(bot_id: str, error_type: str, detail: str):
    """ส่งแจ้งเตือน error ไปที่ CEO ผ่าน LINE ExecCopilot"""
    try:
        # 1. Log ลง monitor
        await monitor.log_message(
            bot_id=bot_id, bot_name=BOTS_CONFIG.get(bot_id, {}).get("name", bot_id),
            sender="SYSTEM", message_in=f"[ERROR] {error_type}",
            message_out=detail[:200], msg_type="error",
            ai_used="none", status="error", response_ms=0,
        )
        # 2. ส่ง LINE Push แจ้ง CEO (ถ้ามี token)
        env = get_env_vars()
        exec_token = env.get("execcopilot", {}).get("token", "")
        ceo_user_id = os.getenv("CEO_LINE_USERID", "")
        if exec_token and ceo_user_id:
            alert_msg = f"[Railway Alert] {bot_id}\n{error_type}: {detail[:300]}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {exec_token}", "Content-Type": "application/json"},
                    json={"to": ceo_user_id, "messages": [{"type": "text", "text": alert_msg}]},
                )
        logger.error(f"[ALERT] {bot_id} — {error_type}: {detail}")
    except Exception as e:
        logger.error(f"Alert send failed: {e}")


async def self_diagnostic() -> Dict:
    """ตรวจสอบระบบทั้งหมด — env vars, API keys, LINE tokens"""
    results = {"timestamp": datetime.now().isoformat(), "checks": {}}

    # ตรวจ API keys
    api_checks = {
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "PERPLEXITY_API_KEY": bool(os.getenv("PERPLEXITY_API_KEY")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "AIRTABLE_PAT": bool(AIRTABLE_PAT),
    }
    results["checks"]["api_keys"] = api_checks

    # ตรวจ LINE tokens
    env = get_env_vars()
    line_checks = {}
    for bot_id, creds in env.items():
        line_checks[bot_id] = {
            "token": bool(creds.get("token")),
            "secret": bool(creds.get("secret")),
        }
    results["checks"]["line_tokens"] = line_checks

    # สรุป
    all_api_ok = all(api_checks.values())
    all_line_ok = all(c["token"] for c in line_checks.values())
    results["healthy"] = all_api_ok and all_line_ok
    results["missing"] = [k for k, v in api_checks.items() if not v]
    results["missing"] += [f"LINE_{k}" for k, v in line_checks.items() if not v["token"]]

    return results


# ==================== Airtable Functions ====================

async def airtable_get_conversation(user_id: str, bot_id: str, limit: int = 10) -> List[Dict]:
    """ดึงประวัติบทสนทนาจาก Airtable"""
    if not AIRTABLE_PAT:
        return []
    try:
        table_id = "ConversationLog"
        formula = f"AND({{UserId}}='{user_id}', {{Bot}}='{bot_id}')"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_id}",
                headers={"Authorization": f"Bearer {AIRTABLE_PAT}"},
                params={
                    "filterByFormula": formula,
                    "sort[0][field]": "Timestamp",
                    "sort[0][direction]": "desc",
                    "maxRecords": limit,
                },
            )
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                records.reverse()
                return [r.get("fields", {}) for r in records]
    except Exception as e:
        logger.warning(f"Airtable get conversation error: {e}")
    return []


async def airtable_save_message(user_id: str, bot_id: str, display_name: str,
                                 message_in: str, message_out: str):
    """บันทึกบทสนทนาลง Airtable"""
    if not AIRTABLE_PAT:
        return
    try:
        table_id = "ConversationLog"
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_id}",
                headers={
                    "Authorization": f"Bearer {AIRTABLE_PAT}",
                    "Content-Type": "application/json",
                },
                json={
                    "records": [{
                        "fields": {
                            "UserId": user_id,
                            "Bot": bot_id,
                            "DisplayName": display_name,
                            "UserMessage": message_in[:1000],
                            "BotResponse": message_out[:2000],
                            "Timestamp": datetime.now().isoformat(),
                        }
                    }]
                },
            )
    except Exception as e:
        logger.warning(f"Airtable save error: {e}")


async def airtable_get_user_profile(user_id: str) -> Optional[Dict]:
    """ดึงข้อมูลผู้ใช้จาก Airtable (Farmers → FarmerRegistration → UnifiedProfiles)"""
    if not AIRTABLE_PAT:
        return None
    try:
        # ค้นหาจากหลายตาราง โดย LINE_UserID
        search_tables = [
            ("Farmers", f"{{LINE_UserID}}='{user_id}'"),
            ("FarmerRegistration", f"{{LINE_UserID}}='{user_id}'"),
        ]
        async with httpx.AsyncClient(timeout=10.0) as client:
            for table, formula in search_tables:
                resp = await client.get(
                    f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}",
                    headers={"Authorization": f"Bearer {AIRTABLE_PAT}"},
                    params={"filterByFormula": formula, "maxRecords": 1},
                )
                if resp.status_code == 200:
                    records = resp.json().get("records", [])
                    if records:
                        fields = records[0].get("fields", {})
                        # Normalize field names for downstream use
                        return {
                            "name": fields.get("Name") or fields.get("FullName", ""),
                            "phone": fields.get("Phone", ""),
                            "crops": fields.get("FruitType", ""),
                            "farmSize": fields.get("AreaRai") or fields.get("Area", ""),
                            "location": fields.get("FarmAddress") or fields.get("District", ""),
                            "notes": fields.get("Notes") or fields.get("FarmCondition", ""),
                            "status": fields.get("Status", ""),
                        }
    except Exception as e:
        logger.warning(f"Airtable user profile error: {e}")
    return None


# ==================== AI Provider Functions ====================

async def call_claude(messages: List[Dict], system: str, bot_id: str) -> Optional[str]:
    """เรียก Claude API — สมองหลัก"""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": CLAUDE_MODEL,
                    "max_tokens": 2048,
                    "system": system,
                    "messages": messages,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("content", [{}])[0].get("text", None)
            else:
                logger.error(f"Claude API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Claude error: {e}")
    return None


async def call_gpt4o_vision(image_url: str, question: str) -> Optional[str]:
    """เรียก GPT-4o Vision สำหรับวิเคราะห์รูปภาพ"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }],
                    "max_tokens": 1024,
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"GPT-4o Vision error: {e}")
    return None


async def call_perplexity(query: str) -> Optional[str]:
    """เรียก Perplexity สำหรับค้นข้อมูล real-time"""
    api_key = os.getenv("PERPLEXITY_API_KEY", "")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": query}],
                },
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Perplexity error: {e}")
    return None


async def call_gemini_fast(message: str) -> Optional[str]:
    """Gemini Flash สำหรับ fallback เร็ว"""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": message}]}]},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini error: {e}")
    return None


# ==================== LINE Functions ====================

async def line_get_content_url(bot_id: str, message_id: str) -> Optional[str]:
    """ดึง URL เนื้อหา (รูป/วิดีโอ) จาก LINE"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    if not token:
        return None
    return f"https://api-data.line.me/v2/bot/message/{message_id}/content"


async def line_get_user_profile(bot_id: str, user_id: str) -> Optional[Dict]:
    """ดึงโปรไฟล์ผู้ใช้จาก LINE"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return None


async def line_reply(bot_id: str, reply_token: str, text: str, user_id: str = ""):
    """ตอบกลับ LINE — ลอง Reply API ก่อน ถ้าล้มเหลวใช้ Push API แทน"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    logger.info(f"[REPLY] bot={bot_id}, has_token={bool(token)}, reply_token={reply_token[:20] if reply_token else 'NONE'}...")
    if not token:
        logger.warning(f"[REPLY] NO TOKEN for {bot_id} — cannot reply!")
        return
    # ตัดข้อความไม่เกิน 5000 ตัวอักษร (LINE limit)
    if len(text) > 4900:
        text = text[:4900] + "..."

    reply_success = False
    # 1. ลอง Reply API ก่อน (ฟรี ไม่เสียโควต้า)
    if reply_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.line.me/v2/bot/message/reply",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
                )
                logger.info(f"[REPLY] Reply API: {resp.status_code} {resp.text[:200]}")
                if resp.status_code == 200:
                    reply_success = True
        except Exception as e:
            logger.error(f"[REPLY] Reply API error: {e}")

    # 2. ถ้า Reply ล้มเหลว ใช้ Push API แทน (เสียโควต้า แต่ดีกว่าไม่ตอบ)
    if not reply_success and user_id:
        logger.warning(f"[REPLY] Reply failed, falling back to Push API for {user_id}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"to": user_id, "messages": [{"type": "text", "text": text}]},
                )
                logger.info(f"[REPLY] Push API fallback: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            logger.error(f"[REPLY] Push API error: {e}")


def verify_line_signature(body: str, secret: str, signature: str) -> bool:
    """ยืนยัน LINE webhook signature"""
    try:
        computed = base64.b64encode(
            hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
        ).decode()
        return hmac.compare_digest(signature, computed)
    except:
        return False


def get_env_vars() -> Dict:
    """ดึง LINE credentials — รองรับทั้งชื่อเก่า (server.js) และชื่อใหม่ (main.py)"""
    return {
        "phrae555": {
            "token": os.getenv("LINE_TOKEN_PHRAE555", "") or os.getenv("PHRAE555_CHANNEL_ACCESS_TOKEN", ""),
            "secret": os.getenv("LINE_SECRET_PHRAE555", "") or os.getenv("PHRAE555_CHANNEL_SECRET", ""),
        },
        "930pchss": {
            "token": os.getenv("LINE_TOKEN_930PCHSS", "") or os.getenv("SALES_CHANNEL_ACCESS_TOKEN", "") or os.getenv("930PCHSS_CHANNEL_ACCESS_TOKEN", ""),
            "secret": os.getenv("LINE_SECRET_930PCHSS", "") or os.getenv("SALES_CHANNEL_SECRET", "") or os.getenv("930PCHSS_CHANNEL_SECRET", ""),
        },
        "aiphrae": {
            "token": os.getenv("LINE_TOKEN_AIPHRAE", "") or os.getenv("AIPHRAE_CHANNEL_ACCESS_TOKEN", "") or os.getenv("PHRAE_CHANNEL_ACCESS_TOKEN", ""),
            "secret": os.getenv("LINE_SECRET_AIPHRAE", "") or os.getenv("AIPHRAE_CHANNEL_SECRET", "") or os.getenv("PHRAE_CHANNEL_SECRET", ""),
        },
        "jewelry": {
            "token": os.getenv("LINE_TOKEN_JEWELRY", "") or os.getenv("JEWELRY_CHANNEL_ACCESS_TOKEN", ""),
            "secret": os.getenv("LINE_SECRET_JEWELRY", "") or os.getenv("JEWELRY_CHANNEL_SECRET", ""),
        },
        "execcopilot": {
            "token": os.getenv("LINE_TOKEN_EXECCOPILOT", "") or os.getenv("EXEC_CHANNEL_ACCESS_TOKEN", "") or os.getenv("EXECCOPILOT_CHANNEL_ACCESS_TOKEN", ""),
            "secret": os.getenv("LINE_SECRET_EXECCOPILOT", "") or os.getenv("EXEC_CHANNEL_SECRET", "") or os.getenv("EXECCOPILOT_CHANNEL_SECRET", ""),
        },
    }


# ==================== Main AI Brain ====================

async def ai_brain(bot_id: str, user_id: str, display_name: str,
                   message_text: str, message_type: str = "text",
                   image_id: str = None) -> str:
    """สมอง AI หลัก — Claude คิด แล้วเรียก AI อื่นตามจำเป็น"""

    bot_config = BOTS_CONFIG.get(bot_id, {})
    system_prompt = bot_config.get("system_prompt", "ตอบภาษาไทย สุภาพ")

    # 1. ดึงประวัติบทสนทนา + โปรไฟล์ผู้ใช้
    history, profile = await asyncio.gather(
        airtable_get_conversation(user_id, bot_id, limit=8),
        airtable_get_user_profile(user_id),
    )

    # 2. สร้าง context เพิ่มเติม
    extra_context = ""
    if profile:
        extra_context += f"\n[ข้อมูลผู้ใช้] ชื่อ: {profile.get('name', display_name)}"
        for key in ['location', 'crops', 'farmSize', 'phone', 'notes']:
            if profile.get(key):
                extra_context += f" | {key}: {profile[key]}"

    # 3. วิเคราะห์รูปภาพ (ถ้ามี)
    image_analysis = ""
    if message_type == "image" and image_id:
        env = get_env_vars()
        token = env.get(bot_id, {}).get("token", "")
        if token:
            # ดาวน์โหลดรูปจาก LINE แล้วส่งให้ GPT-4o
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    img_resp = await client.get(
                        f"https://api-data.line.me/v2/bot/message/{image_id}/content",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if img_resp.status_code == 200:
                        img_base64 = base64.b64encode(img_resp.content).decode()
                        img_data_url = f"data:image/jpeg;base64,{img_base64}"

                        vision_prompt = "วิเคราะห์รูปนี้อย่างละเอียด ถ้าเป็นพืช/ผลไม้ ให้ระบุชนิด สุขภาพ โรค วิธีรักษา ถ้าเป็นพลอย ให้ประเมินสี ความใส คุณภาพ ตอบเป็นภาษาไทย"
                        analysis = await call_gpt4o_vision(img_data_url, vision_prompt)
                        if analysis:
                            image_analysis = f"\n[วิเคราะห์รูปภาพจาก GPT-4o Vision]\n{analysis}"
            except Exception as e:
                logger.error(f"Image analysis error: {e}")

    # 4. ค้นข้อมูล real-time ถ้าจำเป็น (ราคาตลาด สภาพอากาศ)
    search_result = ""
    search_keywords = ["ราคา", "ตลาด", "อากาศ", "ข่าว", "วันนี้", "ล่าสุด", "สภาพ"]
    if any(kw in message_text for kw in search_keywords):
        search_query = f"{message_text} จังหวัดแพร่ ประเทศไทย {datetime.now().strftime('%Y-%m-%d')}"
        result = await call_perplexity(search_query)
        if result:
            search_result = f"\n[ข้อมูล real-time จาก Perplexity]\n{result[:500]}"

    # 5. สร้าง system prompt เต็ม
    full_system = system_prompt
    if extra_context:
        full_system += f"\n\n{extra_context}"
    if image_analysis:
        full_system += f"\n\n{image_analysis}"
    if search_result:
        full_system += f"\n\n{search_result}"

    # 6. สร้าง messages array จากประวัติบทสนทนา
    messages = []
    for h in history:
        if h.get("UserMessage"):
            messages.append({"role": "user", "content": h["UserMessage"]})
        if h.get("BotResponse"):
            messages.append({"role": "assistant", "content": h["BotResponse"]})

    # เพิ่มข้อความปัจจุบัน
    current_msg = message_text
    if message_type == "image":
        current_msg = f"[ผู้ใช้ส่งรูปภาพมา]{' ' + message_text if message_text else ''}"
        if image_analysis:
            current_msg += f"\n{image_analysis}"

    messages.append({"role": "user", "content": f"[{display_name}]: {current_msg}"})

    # 7. เรียก Claude — สมองหลัก
    response = await call_claude(messages, full_system, bot_id)

    # 8. Fallback cascade ถ้า Claude ล้มเหลว
    if not response:
        logger.warning(f"Claude failed for {bot_id}, trying Gemini...")
        response = await call_gemini_fast(
            f"{full_system}\n\nUser: {current_msg}\nAssistant:"
        )

    if not response:
        response = f"ขออภัยค่ะ น้อง{bot_config.get('name', '')} ไม่สามารถตอบได้ในขณะนี้ กรุณาส่งข้อความมาอีกครั้งนะคะ"

    return response


# ==================== Webhook Processing ====================

async def process_webhook_background(bot_id: str, request_body: Dict):
    """Background wrapper — เรียก process_webhook โดยไม่ต้องใช้ BackgroundTasks"""
    try:
        await process_webhook_core(bot_id, request_body)
    except Exception as e:
        logger.error(f"Background webhook error: {e}")

async def process_webhook_core(bot_id: str, request_body: Dict):
    """ประมวลผล LINE webhook — AI ตอบตรง"""
    start_time = time.time()

    events = request_body.get("events", [])
    if not events:
        return

    for event in events:
        event_type = event.get("type", "")

        # รองรับเฉพาะ message events
        if event_type != "message":
            if event_type == "follow":
                logger.info(f"[{bot_id}] New follower: {event.get('source', {}).get('userId', 'unknown')}")
            continue

        # ป้องกันข้อความซ้ำ (LINE retry)
        msg_id_check = event.get("message", {}).get("id", "")
        if msg_id_check and await is_duplicate(f"{bot_id}:{msg_id_check}"):
            logger.warning(f"[DEDUP] Skipping duplicate message {msg_id_check} for {bot_id}")
            continue

        reply_token = event.get("replyToken", "")
        source = event.get("source", {})
        user_id = source.get("userId", "unknown")
        source_type = source.get("type", "user")
        group_id = source.get("groupId", "")

        message = event.get("message", {})
        msg_type = message.get("type", "text")
        msg_text = message.get("text", "")
        msg_id = message.get("id", "")

        # กลุ่ม: ตอบเฉพาะเมื่อถูกเรียกชื่อ
        bot_name = BOTS_CONFIG.get(bot_id, {}).get("name", "")
        if source_type == "group":
            trigger_words = [bot_name, "น้อง", "ai", "AI", "เอไอ", "บอท"]
            if not any(w.lower() in msg_text.lower() for w in trigger_words if w):
                continue  # เงียบ ไม่ตอบเมื่อไม่ถูกเรียก

        # ดึง display name
        profile = await line_get_user_profile(bot_id, user_id)
        display_name = profile.get("displayName", "ท่าน") if profile else "ท่าน"

        # เรียกสมอง AI
        try:
            ai_response = await ai_brain(
                bot_id=bot_id,
                user_id=user_id,
                display_name=display_name,
                message_text=msg_text,
                message_type=msg_type,
                image_id=msg_id if msg_type == "image" else None,
            )
        except Exception as e:
            logger.error(f"AI Brain error: {e}")
            ai_response = f"ขออภัยค่ะ ระบบมีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้งนะคะ"
            # ส่งแจ้งเตือน CEO ทันที
            asyncio.ensure_future(send_error_alert(bot_id, "AI_BRAIN_ERROR", str(e)))

        # ตอบกลับ LINE (Reply API ก่อน → Push API fallback)
        await line_reply(bot_id, reply_token, ai_response, user_id=user_id)

        # บันทึกลง Airtable (non-blocking)
        asyncio.ensure_future(airtable_save_message(
            user_id, bot_id, display_name,
            msg_text if msg_type == "text" else f"[{msg_type}]",
            ai_response,
        ))

        # Log to monitor
        elapsed = (time.time() - start_time) * 1000
        asyncio.ensure_future(monitor.log_message(
            bot_id=bot_id,
            bot_name=bot_name,
            sender=display_name,
            message_in=msg_text[:200],
            message_out=ai_response[:200],
            msg_type=msg_type,
            ai_used="claude",
            status="success",
            response_ms=round(elapsed),
        ))


# ==================== Routes ====================

@app.post("/webhook/{bot_id}")
async def webhook(bot_id: str, request: Request, background_tasks: BackgroundTasks):
    """LINE webhook endpoint"""
    if bot_id not in BOTS_CONFIG:
        raise HTTPException(status_code=400, detail="Invalid bot_id")

    body = await request.body()
    body_str = body.decode("utf-8")

    # Verify signature
    signature = request.headers.get("x-line-signature", "")
    env = get_env_vars()
    secret = env.get(bot_id, {}).get("secret", "")

    if secret and not verify_line_signature(body_str, secret, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    request_body = json.loads(body_str)
    # ตอบ LINE 200 ทันที แล้วประมวลผลใน background
    # ป้องกัน LINE retry ซ้ำ (LINE timeout ~1 วินาที)
    background_tasks.add_task(process_webhook_background, bot_id, request_body)
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.1-multi-ai",
        "brain": "Claude API",
        "vision": "GPT-4o",
        "search": "Perplexity",
        "fallback": "Gemini Flash",
        "database": "Airtable",
        "timestamp": datetime.now().isoformat(),
        "bots": list(BOTS_CONFIG.keys()),
    }


@app.get("/diagnostic")
async def diagnostic():
    """ตรวจสอบระบบทั้งหมด — API keys, LINE tokens, สถานะ"""
    return await self_diagnostic()


@app.get("/monitor", response_class=HTMLResponse)
async def monitor_dashboard():
    logs = await monitor.get_logs(limit=50)
    summary = await monitor.get_summary()
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AI Agent Monitor v2.0</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#1a1a2e;color:#eee;margin:0;padding:20px}}
.container{{max-width:1200px;margin:0 auto}}
h1{{text-align:center;color:#00d4ff;font-size:2em}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:20px 0}}
.stat{{background:#16213e;padding:16px;border-radius:8px;text-align:center}}
.stat h3{{color:#00d4ff;font-size:.8em;margin:0}}
.stat .val{{font-size:2em;font-weight:bold;margin-top:8px}}
.log{{background:#0f3460;padding:10px;margin:6px 0;border-radius:6px;border-left:3px solid #00d4ff}}
.log.success{{border-color:#00ff88}}
.log.failed{{border-color:#ff4444}}
.tag{{background:#00d4ff;color:#000;padding:2px 6px;border-radius:3px;font-size:.8em}}
.time{{color:#888;font-size:.8em}}
</style></head>
<body><div class="container">
<h1>AI Agent Monitor v2.0 — Claude Brain</h1>
<div class="stats">
<div class="stat"><h3>Total Today</h3><div class="val">{summary.get('total',0)}</div></div>
<div class="stat"><h3>Success</h3><div class="val">{summary.get('success',0)}</div></div>
<div class="stat"><h3>Rate</h3><div class="val">{summary.get('success_rate',0):.0f}%</div></div>
</div>
<h2>Recent Messages</h2>
{"".join([f'<div class="log {l.get("status","")}"><span class="tag">{l.get("bot_name","")}</span> <b>{l.get("sender","")}</b>: {l.get("message_in","")[:100]}<br/><span class="time">{l.get("timestamp","")} | {l.get("ai_used","")} | {l.get("response_ms",0)}ms</span></div>' for l in logs])}
</div></body></html>"""
    return html


@app.get("/monitor/api")
async def monitor_api(bot_id: str = None, limit: int = 50):
    logs = await monitor.get_logs(limit=limit, bot_id=bot_id)
    return {"count": len(logs), "logs": logs}


# ==================== Main ====================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)

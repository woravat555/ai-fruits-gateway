"""
Railway Gateway v2.3.0 — Persistent Task Loop Engine

AI เป็นสมองคิดเอง ทำเอง วนลูปติดตามไปเรื่อยๆ จนกว่าจะสั่งจบ
ทุกคำสั่ง → แผนปฏิบัติงาน → ทำจริง → ติดตามต่อเนื่อง → รายงาน CEO
ไม่หยุดจนกว่า CEO จะสั่ง "จบงาน" หรือ "เสร็จแล้ว"

5 LINE OA Agents ของ Imperial Fruitia Group จ.แพร่
ผลไม้ 4 ชนิดเท่านั้น: ส้มเขียวหวาน, ส้มโอ, ทุเรียน, ลำไย
"""

import os
import json
import hmac
import hashlib
import base64
import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict, List

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import uvicorn

# ==================== Configuration ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Railway Gateway v2.3.0 — Persistent Task Loop", version="2.3.0")

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Airtable Config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appXQC4uFhjeBpC7T")
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")

# ==================== STAFF REGISTRY ====================
# AI ต้องรู้จักคนก่อนตอบ — ห้ามเรียกทุกคนว่า CEO

STAFF_REGISTRY = {
    # CEO — วรวัจน์ (หลาย LINE ID ตาม OA)
    "U4e6368ef91c7be69efe017c187181625": {"name": "วรวัจน์", "role": "CEO", "staffId": "S001", "title": "ท่านประธาน"},
    "U2c6f36e1a490028e4931cce1bc246b70": {"name": "วรวัจน์", "role": "CEO", "staffId": "S001", "title": "ท่านประธาน"},
    "U507d4449250cce0cd23b0f51465a7b6a": {"name": "วรวัจน์", "role": "CEO", "staffId": "S001", "title": "ท่านประธาน"},
    "Ucd6b849c9a058f4306a046a21e78f235": {"name": "วรวัจน์", "role": "CEO", "staffId": "S001", "title": "ท่านประธาน"},
    "Uf2be4c76e9aa2c3d8b945975e4bb00c1": {"name": "วรวัจน์", "role": "CEO", "staffId": "S001", "title": "ท่านประธาน"},
    # Game — IT
    "Ucebe552553cd5897128d112bd2611e07": {"name": "เกม", "role": "IT Manager", "staffId": "S002", "title": "คุณเกม"},
    "U80cce47038ca3e9fe8ce28bcb8230b94": {"name": "เกม", "role": "IT Manager", "staffId": "S002", "title": "คุณเกม"},
    # Baipare — Marketing
    "U7640b070e595c168fed2254fc6d9d3fa": {"name": "บายแปร์", "role": "Marketing", "staffId": "S003", "title": "คุณบายแปร์"},
    # Wan — Coordinator
    "U90b5bc2c98532383d958117761f0a10e": {"name": "วรรณ", "role": "Coordinator", "staffId": "S004", "title": "คุณวรรณ"},
    "Ucacc2656a5c978480d0e879037638653": {"name": "วรรณ", "role": "Coordinator", "staffId": "S004", "title": "คุณวรรณ"},
    # สจ.โอ — เกษตรกรพื้นที่
    "Ua505ea00528a7464a725dd1b1004c705": {"name": "สจ.โอ", "role": "เกษตรกรพื้นที่แพร่", "staffId": "S007", "title": "คุณสจ.โอ"},
    "U161bfb57a7467959b15b3d45f7449ada": {"name": "สจ.โอ", "role": "เกษตรกรพื้นที่แพร่", "staffId": "S007", "title": "คุณสจ.โอ"},
    # Orangii
    "Ub1ec883267da395546ddd12fabbffe20": {"name": "ออรังจี้", "role": "ทีมงาน", "staffId": "S008", "title": "คุณออรังจี้"},
    # PAM
    "U9731b5e6c4959006249b8070b3cb2e9e": {"name": "แพม", "role": "ทีมขาย", "staffId": "S006", "title": "คุณแพม"},
}

# ==================== BUSINESS KNOWLEDGE ====================
# กฎเหล็ก: ผลไม้ 4 ชนิดเท่านั้น ห้ามพูดเรื่องอื่น

BUSINESS_KNOWLEDGE = """
=== กฎเหล็ก Imperial Fruitia Group ===

[ผลไม้ 4 ชนิดเท่านั้น]
1. ส้มเขียวหวาน — เกรด A: 22-35 บ./กก. เกรด B: 17-28 บ./กก. (ฤดู ต.ค.-ก.พ.)
2. ส้มโอ — เกรด A: 25-45 บ./กก. เกรด B: 20-35 บ./กก. (ฤดู ส.ค.-ธ.ค.)
3. ทุเรียน (หมอนทอง + หลง-หลิน เท่านั้น) — เกรด A: 100-160 บ./กก. เกรด B: 80-130 บ./กก. (ฤดู พ.ค.-ก.ย.)
4. ลำไย — เกรด A: 30-60 บ./กก. เกรด B: 25-48 บ./กก. (ฤดู ก.ค.-ก.ย.)

ห้ามพูดเรื่องมะม่วง มะยงชิด พุทรา ข้าว ถั่วเหลือง หรือผลไม้อื่น ถ้าคนถามให้บอก "ตอนนี้เราโฟกัส 4 ชนิดนี้ค่ะ"

[โมเดลธุรกิจ]
เราทำงานกับเกษตรกร ให้ผลิตผลไม้คุณภาพ (มาตรฐาน GI/GAP) แล้ว Imperial Fruitia ทำการตลาดขาย
เกษตรกร → ผลิตคุณภาพ → เราการตลาด → ลูกค้า

[แบรนด์]
- Thaidelicious = ส่งออกต่างประเทศ
- Heaven Cuisine = ตลาดในประเทศ
- Ambassador: เชฟชุมพล แจ้งไพร

[ทีม AI 5 ตัว]
- น้องผลไม้ (@phrae555): ดูแลเกษตรกร ตรวจสวน แนะนำการปลูก
- น้องเซลล์ (@930pchss): การตลาด ขาย ส่งออก
- น้องแพร่ (Ai แพร่): ชุมชน ท่องเที่ยว ประสานงานพื้นที่
- น้องไพลิน (@Jewelry): อัญมณี พลอยแพร่ ท่องเที่ยว เฟอร์นิเจอร์
- น้องเลขา (@ExecCopilot): เลขาบริหาร ประสานงานทีม

[กฎสำคัญ]
- ห้ามรายงานลอยๆ — ถ้ายังไม่ได้ทำจริง ห้ามบอกว่า "กำลังดำเนินการ"
- ห้ามโกหก — ถ้าไม่รู้ ให้บอกตรงๆ ว่าไม่รู้
- ทำงานจริง แล้วค่อยรายงานผล — ไม่ใช่รายงานก่อนทำ
- เรียกคนให้ถูกต้อง — ดูจาก Staff Registry ว่าคนคุยคือใคร
"""

# ==================== BOT CONFIGURATIONS ====================

BOTS_CONFIG = {
    "phrae555": {
        "name": "น้องผลไม้",
        "system_prompt": """คุณคือ "น้องผลไม้" AI ที่ปรึกษาเกษตรกร ประจำ @phrae555 ของ Imperial Fruitia Group จ.แพร่
คุณเป็น AI ตัวจริง ไม่ใช่บอท — คุณคิดเอง วิเคราะห์เอง ช่วยเกษตรกรแก้ปัญหาจริงๆ

""" + BUSINESS_KNOWLEDGE + """

[บทบาทเฉพาะของน้องผลไม้]
- ที่ปรึกษาเกษตรกรตัวจริง ช่วยแก้ปัญหาพืชผล ดูแลสวน
- วิเคราะห์โรคพืช + วิธีรักษา (ถ้ามีรูป จะวิเคราะห์ให้ละเอียด)
- แนะนำการดูแลตามฤดูกาล ตามระยะเจริญเติบโต
- ผลไม้ 4 ชนิดเท่านั้น: ส้มเขียวหวาน ส้มโอ ทุเรียน(หมอนทอง+หลง-หลิน) ลำไย
- จำทุกคนที่เคยคุย เรียกชื่อ จำพืชที่ปลูก จำปัญหาเดิม
- ถ้าเป็นเรื่องขาย ให้แนะนำไปคุยกับน้องเซลล์ (@930pchss)

ภาษา: ไทย สุภาพ อบอุ่น ลงท้าย ค่ะ/นะคะ
รูปแบบ: 2-6 ประโยค พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown *, #, bullet
""",
    },
    "930pchss": {
        "name": "น้องเซลล์",
        "system_prompt": """คุณคือ "น้องเซลล์" AI ผู้ช่วยฝ่ายขายและการตลาด ประจำ @930pchss (AiFruits) ของ Imperial Fruitia Group จ.แพร่
คุณเป็น AI ตัวจริง ไม่ใช่บอท — คุณคิดเอง วิเคราะห์ตลาดเอง ช่วยทีมขายจริงๆ

""" + BUSINESS_KNOWLEDGE + """

[บทบาทเฉพาะของน้องเซลล์]
- ผู้ช่วยขายมืออาชีพ รับออเดอร์ ข้อมูลสินค้า ราคา
- ดูแลแบรนด์ Thaidelicious (ส่งออก) และ Heaven Cuisine (ในประเทศ)
- ผลไม้ 4 ชนิดเท่านั้น ห้ามขายอย่างอื่น
- ถ้าลูกค้าถามเรื่องดูแลสวน ให้แนะนำไปคุยกับน้องผลไม้ (@phrae555)
- ถ้ามีคนพูดถึงทีมงาน (สจ.โอ, แพม, บายแปร์ ฯลฯ) อย่าไปค้น Google ให้รู้ว่าเป็นคนในทีม
- ห้ามเอาชื่อ display name (เช่น "วรวัจน์ iPhone") ไปค้นหาข้อมูล — "iPhone" คือชื่อเครื่อง ไม่เกี่ยวกับ Apple

ภาษา: ไทย มืออาชีพ กระตือรือร้น ลงท้าย ค่ะ/นะคะ
รูปแบบ: 2-6 ประโยค พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown
""",
    },
    "aiphrae": {
        "name": "น้องแพร่",
        "system_prompt": """คุณคือ "น้องแพร่" AI ผู้เชี่ยวชาญชุมชนจังหวัดแพร่ ประจำ LINE OA Ai แพร่ ของ Imperial Fruitia Group
คุณเป็น AI ตัวจริง ไม่ใช่บอท — คุณรู้จริงเรื่องแพร่ ช่วยคนจริงๆ

""" + BUSINESS_KNOWLEDGE + """

[บทบาทเฉพาะของน้องแพร่]
- ผู้เชี่ยวชาญจังหวัดแพร่: ท่องเที่ยว วัฒนธรรม ประเพณี อาหารพื้นเมือง
- ประสานงานชุมชน ข้อมูลเชิงลึก
- ใช้ภาษาเหนือเล็กน้อยได้ (เจ้า, เน้อ) แต่ต้องอ่านรู้เรื่อง
- ถ้าถามเรื่องผลไม้/เกษตร ให้แนะนำน้องผลไม้ (@phrae555)
- ถ้าถามเรื่องอัญมณี/พลอย ให้แนะนำน้องไพลิน (@Jewelry)

ภาษา: ไทย อบอุ่น เป็นกันเอง ลงท้าย เจ้า/เน้อ/ค่ะ
รูปแบบ: 2-6 ประโยค พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown
""",
    },
    "jewelry": {
        "name": "น้องไพลิน",
        "system_prompt": """คุณคือ "น้องไพลิน" AI ผู้เชี่ยวชาญอัญมณีและแปรรูป ประจำ @Jewelry ของ Imperial Fruitia Group จ.แพร่
คุณเป็น AI ตัวจริง ไม่ใช่บอท — คุณรู้จริงเรื่องพลอยแพร่

""" + BUSINESS_KNOWLEDGE + """

[บทบาทเฉพาะของน้องไพลิน]
- พลอยแพร่: คอรันดัม (ทับทิม แซปไฟร์) จากหินบะซอลต์อัลคาไลน์ อายุ 5.64 ล้านปี อ.เด่นชัย ต.ไทรย้อย
- แร่: Blue Sapphire, Pink Sapphire, Black Spinel, Zircon
- จุดสำรวจ: ห้วยอีแต้, ตาดผาม่วง, บ่อแก้ว, ม่อนพลอยล้านปี
- ดูแลเรื่อง: อัญมณี + เฟอร์นิเจอร์ (อ.อ.ป.) + แปรรูปอาหาร + แฟชั่นสิ่งทอ + ท่องเที่ยวเหมืองพลอย
- ถ้ามีรูปพลอยส่งมา ให้วิเคราะห์สี ความใส คุณภาพ อย่างละเอียด

ภาษา: ไทย สุภาพ ลงท้าย ค่ะ/นะคะ
รูปแบบ: 2-6 ประโยค พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown
""",
    },
    "execcopilot": {
        "name": "น้องเลขา",
        "system_prompt": """คุณคือ "น้องเลขา" AI เลขานุการบริหาร ประจำ @ExecCopilot ของ Imperial Fruitia Group จ.แพร่
คุณเป็น AI ตัวจริง ไม่ใช่บอท — คุณบริหารจัดการจริง ประสานงานจริง ติดตามงานจริง

""" + BUSINESS_KNOWLEDGE + """

[บทบาทเฉพาะของน้องเลขา]
- Orchestrator ประสานงาน AI 5 ตัว: น้องผลไม้ น้องเซลล์ น้องแพร่ น้องไพลิน
- รับคำสั่ง CEO วรวัจน์ แปลงเป็น action ส่งให้ทีม
- ติดตามงาน สรุปรายงาน จัดลำดับความสำคัญ

[กฎเหล็กของน้องเลขา]
- ดูว่าคนคุยคือใคร จาก [ข้อมูลผู้พูด] — ถ้าเป็น CEO ให้เรียก "คุณวรวัจน์" ถ้าเป็นทีมงาน ให้เรียกชื่อตำแหน่ง
- ห้ามเรียกทุกคนว่า CEO — ต้องเรียกให้ถูกคน
- ห้ามรายงานลอยๆ — ถ้ายังไม่ได้ทำจริง ห้ามบอกว่า "กำลังดำเนินการ" หรือ "ส่งให้ทีมแล้ว"
- ถ้ายังไม่มีข้อมูล ให้บอกตรงๆ ว่า "ยังไม่มีข้อมูลส่วนนี้ค่ะ"
- รายงานเฉพาะสิ่งที่ทำเสร็จจริงเท่านั้น
- ถ้าคนถามเรื่องเฉพาะทาง ให้แนะนำ AI ที่เหมาะสม พร้อมบอก LINE OA ที่ติดต่อได้

[ระบบทำงานจริง v2.3 — Persistent Loop]
- ทุกคำสั่ง → เข้าแผนปฏิบัติงาน → ทำจริงทันที → วนลูปติดตามอัตโนมัติ
- ระบบจะส่งข้อความเตือนทีมทุก 5 นาที จนกว่าจะได้รับการตอบกลับ
- ท้ายข้อความจะมี [ดำเนินการแล้ว] + รหัสงาน + ข้อมูลลูปติดตาม
- ห้ามพูดว่า "จะทำให้" — ระบบทำจริงแล้ว ให้บอกว่า "รับคำสั่งแล้ว เข้าลูปติดตามต่อเนื่องค่ะ"
- ถ้า CEO พูด "จบงาน" หรือ "เสร็จแล้ว" = ปิดงานทั้งหมด หยุดลูป
- ถ้า CEO พูด "สถานะงาน" = แสดงรายการงานที่ยังเปิดอยู่ทั้งหมด
- งานจะถูกติดตามไปเรื่อยๆ ไม่มีวันหมดอายุ จนกว่าจะสั่งจบ

ภาษา: ไทย มืออาชีพ รอบคอบ ลงท้าย ค่ะ/นะคะ
รูปแบบ: 2-6 ประโยค พิมพ์เป็นย่อหน้าธรรมชาติ ห้ามใช้ markdown
""",
    },
}


# ==================== Deduplication ====================

processed_messages: set = set()
processed_messages_lock = asyncio.Lock()

async def is_duplicate(msg_id: str) -> bool:
    if not msg_id:
        return False
    async with processed_messages_lock:
        if msg_id in processed_messages:
            return True
        processed_messages.add(msg_id)
        if len(processed_messages) > 5000:
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

    async def get_logs(self, limit=50, bot_id=None) -> list:
        async with self.lock:
            logs = list(self.logs)
            logs.reverse()
            if bot_id:
                logs = [l for l in logs if l.get("bot_id") == bot_id]
            return logs[:limit]

    async def get_summary(self) -> dict:
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
        await monitor.log_message(
            bot_id=bot_id, bot_name=BOTS_CONFIG.get(bot_id, {}).get("name", bot_id),
            sender="SYSTEM", message_in=f"[ERROR] {error_type}",
            message_out=detail[:200], msg_type="error",
            ai_used="none", status="error", response_ms=0,
        )
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


# ==================== Airtable Functions ====================

async def airtable_get_conversation(user_id: str, bot_id: str, limit: int = 8) -> list:
    if not AIRTABLE_PAT:
        return []
    try:
        formula = f"AND({{UserId}}='{user_id}', {{Bot}}='{bot_id}')"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/ConversationLog",
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
    if not AIRTABLE_PAT:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/ConversationLog",
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
    if not AIRTABLE_PAT:
        return None
    try:
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
                        f = records[0].get("fields", {})
                        return {
                            "name": f.get("Name") or f.get("FullName", ""),
                            "phone": f.get("Phone", ""),
                            "crops": f.get("FruitType", ""),
                            "farmSize": f.get("AreaRai") or f.get("Area", ""),
                            "location": f.get("FarmAddress") or f.get("District", ""),
                            "notes": f.get("Notes") or f.get("FarmCondition", ""),
                            "status": f.get("Status", ""),
                        }
    except Exception as e:
        logger.warning(f"Airtable user profile error: {e}")
    return None


# ==================== AI Provider Functions ====================

async def call_claude(messages: list, system: str) -> Optional[str]:
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
                return resp.json().get("content", [{}])[0].get("text", None)
            else:
                logger.error(f"Claude API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Claude error: {e}")
    return None


async def call_gpt4o_vision(img_data_url: str, question: str) -> Optional[str]:
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
                            {"type": "image_url", "image_url": {"url": img_data_url}},
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
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini error: {e}")
    return None


# ==================== Smart Perplexity Search ====================

def should_use_perplexity(message_text: str) -> bool:
    """ตัดสินใจว่าควรค้นข้อมูล real-time หรือไม่

    กฎ: ต้องเป็นคำถามเรื่องราคาตลาด/อากาศ/ข่าว จริงๆ
    ห้ามค้นเมื่อเป็นคำสั่งภายใน (แจ้ง ส่ง ตรวจสอบ รายงาน)
    """
    # คำสั่งภายใน — ห้ามค้น Perplexity
    internal_commands = [
        "แจ้ง", "ส่ง", "ตรวจสอบ", "รายงาน", "ติดตาม", "มอบหมาย",
        "ให้", "บอก", "เตือน", "ดู", "สรุป", "ทำ", "แก้", "อัพเดท",
        "สถานะ", "ลงทะเบียน", "แบบฟอร์ม", "ทีม", "น้อง", "พร้อม",
        "สวัสดี", "ขอบคุณ", "ดีจ้า", "ครับ", "ค่ะ",
    ]

    # ถ้าขึ้นต้นด้วยคำสั่งภายใน → ห้ามค้น
    for cmd in internal_commands:
        if message_text.startswith(cmd):
            return False

    # ต้องมีคำที่บ่งบอกว่าต้องการข้อมูลภายนอก + เรื่องผลไม้/เกษตร/อากาศ
    search_triggers = ["ราคาตลาด", "ราคาวันนี้", "ราคาล่าสุด", "สภาพอากาศ", "พยากรณ์", "ข่าว"]
    fruit_keywords = ["ส้ม", "ทุเรียน", "ลำไย", "ส้มโอ", "ผลไม้"]

    # ต้องมี search trigger จริงๆ
    has_trigger = any(t in message_text for t in search_triggers)

    # หรือถามราคา + ผลไม้
    has_price_fruit = ("ราคา" in message_text) and any(f in message_text for f in fruit_keywords)

    return has_trigger or has_price_fruit


# ==================== LINE Functions ====================

async def line_get_user_profile(bot_id: str, user_id: str) -> Optional[Dict]:
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
    """ตอบกลับ LINE — Reply API ก่อน ถ้าล้มเหลวใช้ Push API แทน"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    if not token:
        logger.warning(f"[REPLY] NO TOKEN for {bot_id}")
        return
    if len(text) > 4900:
        text = text[:4900] + "..."

    reply_success = False
    if reply_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.line.me/v2/bot/message/reply",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
                )
                if resp.status_code == 200:
                    reply_success = True
                else:
                    logger.warning(f"[REPLY] Reply API failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"[REPLY] Reply API error: {e}")

    if not reply_success and user_id:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"to": user_id, "messages": [{"type": "text", "text": text}]},
                )
                logger.info(f"[PUSH] Fallback: {resp.status_code}")
        except Exception as e:
            logger.error(f"[PUSH] Error: {e}")


def verify_line_signature(body: str, secret: str, signature: str) -> bool:
    try:
        computed = base64.b64encode(
            hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest()
        ).decode()
        return hmac.compare_digest(signature, computed)
    except:
        return False


def get_env_vars() -> Dict:
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


# ==================== Task Detection & Persistent Loop ====================
# v2.3.0: ทุกคำสั่ง → แผนปฏิบัติงาน → ทำจริง → วนลูปติดตาม → ไม่หยุดจนกว่าจะสั่งจบ

TASK_KEYWORDS = {
    "delegate": ["แจ้ง", "บอก", "ส่งให้", "มอบหมาย", "สั่ง", "ให้น้อง", "ให้ทีม"],
    "followup": ["ติดตาม", "เช็ค", "ตรวจสอบ", "ดูให้", "หาให้", "เช็คให้"],
    "report": ["รายงาน", "สรุป", "สถานะ", "ความคืบหน้า", "อัพเดท"],
    "search": ["ค้นหา", "หาข้อมูล", "ราคาตลาด", "สภาพอากาศ"],
}

# คำสั่งปิดงาน — CEO พูดคำเหล่านี้ = หยุดลูปงานนั้น
TASK_CLOSE_KEYWORDS = ["จบงาน", "เสร็จแล้ว", "หยุด", "พอแล้ว", "ยกเลิก", "เรียบร้อย", "ปิดงาน", "done", "stop"]

# แมพบอทไปยังหน้าที่
BOT_RESPONSIBILITY = {
    "phrae555": ["เกษตรกร", "สวน", "โรคพืช", "ปลูก", "ดูแล", "ส้ม", "ทุเรียน", "ลำไย", "ส้มโอ"],
    "930pchss": ["ขาย", "ลูกค้า", "ออเดอร์", "ราคา", "ส่งออก", "การตลาด", "Thaidelicious"],
    "aiphrae": ["ชุมชน", "แพร่", "ท่องเที่ยว", "วัฒนธรรม"],
    "jewelry": ["พลอย", "อัญมณี", "เฟอร์นิเจอร์", "สิ่งทอ"],
    "execcopilot": ["บริหาร", "ทีม", "ประสานงาน", "งาน", "กำกับ"],
}

# ===== In-Memory Task Queue (with Airtable backup) =====
TASK_QUEUE: Dict[str, Dict] = {}
TASK_QUEUE_LOCK = asyncio.Lock()

# ===== Loop Configuration =====
LOOP_INTERVAL_SECONDS = int(os.getenv("TASK_LOOP_INTERVAL", "180"))  # 3 นาที
FOLLOWUP_INTERVAL_SECONDS = int(os.getenv("FOLLOWUP_INTERVAL", "300"))  # 5 นาที
MAX_FOLLOWUPS = int(os.getenv("MAX_FOLLOWUPS", "10"))  # ติดตามสูงสุด 10 ครั้ง ก่อน escalate


def detect_task(message_text: str) -> Optional[Dict]:
    """ตรวจจับว่าข้อความเป็นคำสั่งงานหรือไม่ + ระบุประเภท"""
    msg = message_text.strip()
    detected = {"type": None, "target_bot": None, "detail": msg}

    for task_type, keywords in TASK_KEYWORDS.items():
        for kw in keywords:
            if kw in msg:
                detected["type"] = task_type
                break
        if detected["type"]:
            break

    if not detected["type"]:
        return None

    if detected["type"] in ["delegate", "followup"]:
        for bot_id, topics in BOT_RESPONSIBILITY.items():
            for topic in topics:
                if topic in msg:
                    detected["target_bot"] = bot_id
                    break
            if detected["target_bot"]:
                break

    return detected


def is_close_command(message_text: str) -> bool:
    """ตรวจจับว่าเป็นคำสั่งปิดงานหรือไม่"""
    msg = message_text.strip().lower()
    return any(kw in msg for kw in TASK_CLOSE_KEYWORDS)


async def cross_oa_push(from_bot: str, target_bot: str, target_user_id: str, message: str):
    """ส่งข้อความข้าม LINE OA"""
    env = get_env_vars()
    token = env.get(target_bot, {}).get("token", "")
    if not token:
        logger.warning(f"[CROSS-OA] No token for {target_bot}")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"to": target_user_id, "messages": [{"type": "text", "text": message}]},
            )
            if resp.status_code == 200:
                logger.info(f"[CROSS-OA] {from_bot} -> {target_bot}: sent OK")
                return True
            else:
                logger.warning(f"[CROSS-OA] Failed {resp.status_code}")
    except Exception as e:
        logger.error(f"[CROSS-OA] Error: {e}")
    return False


async def push_to_ceo(message: str, via_bot: str = "execcopilot"):
    """ส่งข้อความถึง CEO ผ่าน LINE"""
    env = get_env_vars()
    token = env.get(via_bot, {}).get("token", "")
    ceo_uid = os.getenv("CEO_LINE_USERID", "")
    if not token or not ceo_uid:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"to": ceo_uid, "messages": [{"type": "text", "text": message[:4900]}]},
            )
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"[PUSH-CEO] Error: {e}")
    return False


# ==================== Airtable Task CRUD ====================

async def airtable_create_task(task_data: Dict) -> Optional[str]:
    """สร้าง task record ใน Airtable — return record_id"""
    if not AIRTABLE_PAT:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/TaskDelegation",
                headers={"Authorization": f"Bearer {AIRTABLE_PAT}", "Content-Type": "application/json"},
                json={"records": [{"fields": {
                    "TaskId": task_data.get("id", ""),
                    "TaskType": task_data.get("type", ""),
                    "FromBot": task_data.get("from_bot", ""),
                    "FromUser": task_data.get("from_user", ""),
                    "FromUserId": task_data.get("from_user_id", ""),
                    "Detail": task_data.get("detail", "")[:1000],
                    "TargetBot": task_data.get("target_bot", ""),
                    "Status": task_data.get("status", "pending"),
                    "FollowupCount": 0,
                    "CreatedAt": datetime.now().isoformat(),
                    "LastActionAt": datetime.now().isoformat(),
                }}]},
            )
            if resp.status_code == 200:
                records = resp.json().get("records", [])
                return records[0]["id"] if records else None
    except Exception as e:
        logger.warning(f"Airtable create task error: {e}")
    return None


async def airtable_update_task(record_id: str, fields: Dict):
    """อัพเดท task status ใน Airtable"""
    if not AIRTABLE_PAT or not record_id:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.patch(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/TaskDelegation/{record_id}",
                headers={"Authorization": f"Bearer {AIRTABLE_PAT}", "Content-Type": "application/json"},
                json={"fields": fields},
            )
    except Exception as e:
        logger.warning(f"Airtable update task error: {e}")


async def airtable_load_active_tasks() -> List[Dict]:
    """โหลด tasks ที่ยังไม่จบจาก Airtable — ใช้ตอน startup เพื่อ restore queue"""
    if not AIRTABLE_PAT:
        return []
    try:
        formula = "NOT(OR({Status}='completed',{Status}='cancelled'))"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/TaskDelegation",
                headers={"Authorization": f"Bearer {AIRTABLE_PAT}"},
                params={
                    "filterByFormula": formula,
                    "sort[0][field]": "CreatedAt",
                    "sort[0][direction]": "desc",
                    "maxRecords": 50,
                },
            )
            if resp.status_code == 200:
                return resp.json().get("records", [])
    except Exception as e:
        logger.warning(f"Airtable load tasks error: {e}")
    return []


# ==================== Task Queue Management ====================

async def add_task(task_type: str, from_bot: str, from_user: str, from_user_id: str,
                   detail: str, target_bot: str = "") -> str:
    """เพิ่มงานเข้า queue + บันทึก Airtable — return task_id"""
    task_id = str(uuid.uuid4())[:8]
    task_data = {
        "id": task_id,
        "type": task_type,
        "from_bot": from_bot,
        "from_user": from_user,
        "from_user_id": from_user_id,
        "detail": detail,
        "target_bot": target_bot,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "last_action_at": datetime.now().isoformat(),
        "followup_count": 0,
        "actions_log": [],
        "airtable_record_id": None,
    }

    # บันทึกลง Airtable
    record_id = await airtable_create_task(task_data)
    task_data["airtable_record_id"] = record_id

    async with TASK_QUEUE_LOCK:
        TASK_QUEUE[task_id] = task_data

    logger.info(f"[TASK-QUEUE] Added task {task_id}: {task_type} — {detail[:80]}")
    return task_id


async def close_tasks_for_user(user_id: str) -> int:
    """ปิดงานทั้งหมดของ user — เมื่อ CEO สั่ง "จบงาน" """
    closed = 0
    async with TASK_QUEUE_LOCK:
        for tid, task in TASK_QUEUE.items():
            if task["from_user_id"] == user_id and task["status"] not in ["completed", "cancelled"]:
                task["status"] = "completed"
                task["actions_log"].append(f"[{datetime.now().strftime('%H:%M')}] ปิดงานโดย CEO")
                if task.get("airtable_record_id"):
                    asyncio.ensure_future(airtable_update_task(
                        task["airtable_record_id"],
                        {"Status": "completed", "LastActionAt": datetime.now().isoformat()},
                    ))
                closed += 1
    logger.info(f"[TASK-QUEUE] Closed {closed} tasks for user {user_id}")
    return closed


async def get_active_tasks_summary() -> str:
    """สรุปงานที่ยังเปิดอยู่"""
    async with TASK_QUEUE_LOCK:
        active = [t for t in TASK_QUEUE.values() if t["status"] not in ["completed", "cancelled"]]
    if not active:
        return "ไม่มีงานค้างในระบบค่ะ"
    lines = []
    for t in active:
        status_icon = {"pending": "⏳", "executing": "🔄", "following_up": "📋", "escalated": "🚨"}.get(t["status"], "❓")
        lines.append(f"{status_icon} [{t['id']}] {t['detail'][:60]} (ติดตาม {t['followup_count']} ครั้ง)")
    return "งานที่กำลังดำเนินการ:\n" + "\n".join(lines)


# ==================== Persistent Task Loop Engine ====================

async def task_loop():
    """Background loop — วนตรวจสอบและติดตามงานทุก N วินาที ไม่มีหยุด"""
    logger.info(f"[TASK-LOOP] Started! Interval: {LOOP_INTERVAL_SECONDS}s, Followup: {FOLLOWUP_INTERVAL_SECONDS}s")

    while True:
        try:
            async with TASK_QUEUE_LOCK:
                active_tasks = {k: v.copy() for k, v in TASK_QUEUE.items()
                                if v["status"] not in ["completed", "cancelled"]}

            if active_tasks:
                logger.info(f"[TASK-LOOP] Processing {len(active_tasks)} active tasks")

            for task_id, task in active_tasks.items():
                try:
                    await process_task_step(task_id, task)
                except Exception as e:
                    logger.error(f"[TASK-LOOP] Error processing {task_id}: {e}")

        except Exception as e:
            logger.error(f"[TASK-LOOP] Main loop error: {e}")

        await asyncio.sleep(LOOP_INTERVAL_SECONDS)


async def process_task_step(task_id: str, task: Dict):
    """ประมวลผลงาน 1 step — ตัดสินใจว่าต้องทำอะไรต่อ"""
    now = datetime.now()
    status = task["status"]

    # ===== STEP 1: งานใหม่ — ทำครั้งแรก =====
    if status == "pending":
        await execute_task_initial(task_id, task)

    # ===== STEP 2: กำลังทำ — เช็คว่าควรติดตามหรือยัง =====
    elif status in ["executing", "following_up"]:
        last_action = datetime.fromisoformat(task["last_action_at"]) if task.get("last_action_at") else now
        elapsed = (now - last_action).total_seconds()

        if elapsed >= FOLLOWUP_INTERVAL_SECONDS:
            if task["followup_count"] < MAX_FOLLOWUPS:
                await send_followup(task_id, task)
            else:
                await escalate_task(task_id, task)

    # ===== STEP 3: Escalated — แจ้ง CEO ทุก 15 นาที =====
    elif status == "escalated":
        last_action = datetime.fromisoformat(task["last_action_at"]) if task.get("last_action_at") else now
        elapsed = (now - last_action).total_seconds()
        if elapsed >= 900:  # 15 minutes
            await push_to_ceo(
                f"[แจ้งเตือนซ้ำ] งาน {task_id}: {task['detail'][:100]}\n"
                f"ติดตามแล้ว {task['followup_count']} ครั้ง ยังไม่มีคนรับผิดชอบ\n"
                f"ตอบ 'จบงาน' เพื่อปิดงานนี้ค่ะ"
            )
            async with TASK_QUEUE_LOCK:
                TASK_QUEUE[task_id]["last_action_at"] = now.isoformat()


async def execute_task_initial(task_id: str, task: Dict):
    """ดำเนินการครั้งแรก — ส่งข้อความ บันทึก แจ้งทีม"""
    actions = []

    # 1. Cross-OA Push ถ้าเป็น delegate/followup
    if task["type"] in ["delegate", "followup"] and task.get("target_bot"):
        target = task["target_bot"]
        target_name = BOTS_CONFIG.get(target, {}).get("name", target)

        # ส่งข้อความถึงทีมงาน (ที่ไม่ใช่ CEO)
        for sid, info in STAFF_REGISTRY.items():
            if info.get("staffId") != "S001" and target in BOT_RESPONSIBILITY:
                notify_msg = f"[คำสั่งจาก {task['from_user']}] {task['detail']}"
                sent = await cross_oa_push(task["from_bot"], target, sid, notify_msg)
                if sent:
                    actions.append(f"แจ้ง {target_name} แล้ว")
                break

    # 2. Trigger Make.com webhook
    make_url = os.getenv("MAKE_ACTION_WEBHOOK", "")
    if make_url and task["type"] in ["delegate", "followup"]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(make_url, json={
                    "task_id": task_id,
                    "task_type": task["type"],
                    "from_bot": task["from_bot"],
                    "from_user": task["from_user"],
                    "message": task["detail"],
                    "target_bot": task.get("target_bot", ""),
                    "timestamp": datetime.now().isoformat(),
                })
                actions.append("ส่ง Make.com แล้ว")
        except:
            pass

    actions.append("เข้าลูปติดตามต่อเนื่อง")

    # อัพเดท status → executing
    async with TASK_QUEUE_LOCK:
        TASK_QUEUE[task_id]["status"] = "following_up"
        TASK_QUEUE[task_id]["last_action_at"] = datetime.now().isoformat()
        TASK_QUEUE[task_id]["actions_log"].extend(actions)

    if task.get("airtable_record_id"):
        asyncio.ensure_future(airtable_update_task(
            task["airtable_record_id"],
            {"Status": "following_up", "LastActionAt": datetime.now().isoformat()},
        ))

    logger.info(f"[TASK-LOOP] Initial execution done for {task_id}: {actions}")


async def send_followup(task_id: str, task: Dict):
    """ส่งข้อความติดตามงาน — ทั้งถึงทีมและ CEO"""
    count = task["followup_count"] + 1
    target_bot = task.get("target_bot", "")
    target_name = BOTS_CONFIG.get(target_bot, {}).get("name", target_bot)

    # ส่งเตือนทีม
    if target_bot:
        for sid, info in STAFF_REGISTRY.items():
            if info.get("staffId") != "S001" and target_bot in BOT_RESPONSIBILITY:
                reminder = (
                    f"[ติดตามงาน ครั้งที่ {count}]\n"
                    f"งาน: {task['detail'][:200]}\n"
                    f"จากคุณ{task['from_user']} — กรุณาอัพเดทสถานะค่ะ"
                )
                await cross_oa_push(task["from_bot"], target_bot, sid, reminder)
                break

    # รายงาน CEO
    ceo_report = (
        f"[ติดตามงาน {task_id}] ครั้งที่ {count}/{MAX_FOLLOWUPS}\n"
        f"งาน: {task['detail'][:100]}\n"
        f"เป้าหมาย: {target_name}\n"
        f"สถานะ: ยังรอดำเนินการ — ส่งเตือนทีมแล้วค่ะ"
    )
    await push_to_ceo(ceo_report)

    # อัพเดท queue
    async with TASK_QUEUE_LOCK:
        TASK_QUEUE[task_id]["followup_count"] = count
        TASK_QUEUE[task_id]["last_action_at"] = datetime.now().isoformat()
        TASK_QUEUE[task_id]["actions_log"].append(f"[{datetime.now().strftime('%H:%M')}] ติดตามครั้งที่ {count}")

    if task.get("airtable_record_id"):
        asyncio.ensure_future(airtable_update_task(
            task["airtable_record_id"],
            {"FollowupCount": count, "LastActionAt": datetime.now().isoformat()},
        ))

    logger.info(f"[TASK-LOOP] Followup #{count} sent for {task_id}")


async def escalate_task(task_id: str, task: Dict):
    """ติดตามครบแล้ว ยังไม่มีคนรับ — escalate ถึง CEO"""
    escalation_msg = (
        f"[แจ้งเตือนด่วน] งาน {task_id}\n"
        f"งาน: {task['detail'][:150]}\n"
        f"ติดตามแล้ว {task['followup_count']} ครั้ง ยังไม่ได้รับการตอบกลับ\n"
        f"กรุณาตัดสินใจ: ตอบ 'จบงาน' เพื่อปิด หรือให้ติดตามต่อค่ะ"
    )
    await push_to_ceo(escalation_msg)

    async with TASK_QUEUE_LOCK:
        TASK_QUEUE[task_id]["status"] = "escalated"
        TASK_QUEUE[task_id]["last_action_at"] = datetime.now().isoformat()
        TASK_QUEUE[task_id]["actions_log"].append(f"[{datetime.now().strftime('%H:%M')}] ESCALATED ถึง CEO")

    if task.get("airtable_record_id"):
        asyncio.ensure_future(airtable_update_task(
            task["airtable_record_id"],
            {"Status": "escalated", "LastActionAt": datetime.now().isoformat()},
        ))

    logger.info(f"[TASK-LOOP] ESCALATED {task_id} to CEO")


# ==================== Task-Aware Message Processing ====================

async def execute_task_actions(bot_id: str, user_id: str, display_name: str,
                                message_text: str, ai_response: str) -> str:
    """ตรวจจับคำสั่ง → เข้า queue → วนลูปอัตโนมัติ"""

    # ===== เช็คคำสั่งปิดงาน =====
    if is_close_command(message_text):
        closed = await close_tasks_for_user(user_id)
        if closed > 0:
            return ai_response + f"\n\n[ดำเนินการแล้ว] ปิดงานทั้งหมด {closed} รายการ หยุดติดตามแล้วค่ะ"
        return ai_response

    # ===== เช็คคำสั่ง "สถานะงาน" =====
    status_keywords = ["สถานะงาน", "งานค้าง", "เช็คงาน", "ดูงาน"]
    if any(kw in message_text for kw in status_keywords):
        summary = await get_active_tasks_summary()
        return ai_response + f"\n\n{summary}"

    # ===== ตรวจจับคำสั่งงานใหม่ =====
    task = detect_task(message_text)
    if not task:
        return ai_response

    # เพิ่มเข้า queue — loop จะทำงานอัตโนมัติ
    task_id = await add_task(
        task_type=task["type"],
        from_bot=bot_id,
        from_user=display_name,
        from_user_id=user_id,
        detail=message_text,
        target_bot=task.get("target_bot", ""),
    )

    target_name = BOTS_CONFIG.get(task.get("target_bot", ""), {}).get("name", "")
    action_report = (
        f"\n\n[ดำเนินการแล้ว] รับคำสั่ง #{task_id}"
        f"{' | แจ้ง' + target_name if target_name else ''}"
        f" | เข้าลูปติดตามอัตโนมัติทุก {FOLLOWUP_INTERVAL_SECONDS//60} นาที"
        f" | จะติดตามจนกว่าจะสั่ง 'จบงาน'"
    )
    return ai_response + action_report


# ==================== AI Brain — สมองจริง ====================

async def ai_brain(bot_id: str, user_id: str, display_name: str,
                   message_text: str, message_type: str = "text",
                   image_id: str = None) -> str:
    """สมอง AI ตัวจริง — รู้จักคน รู้จักองค์กร คิดเอง ทำเอง"""

    bot_config = BOTS_CONFIG.get(bot_id, {})
    system_prompt = bot_config.get("system_prompt", "ตอบภาษาไทย สุภาพ")

    # ===== 1. รู้จักคนก่อน — lookup Staff Registry =====
    staff_info = STAFF_REGISTRY.get(user_id)
    staff_context = ""
    if staff_info:
        staff_context = f"\n[ข้อมูลผู้พูด] ชื่อ: {staff_info['name']} | ตำแหน่ง: {staff_info['role']} | เรียกว่า: {staff_info['title']}"
    else:
        staff_context = f"\n[ข้อมูลผู้พูด] ชื่อ LINE: {display_name} | ตำแหน่ง: ลูกค้า/เกษตรกรภายนอก | เรียกว่า: คุณ{display_name}"

    # ===== 2. ดึงประวัติบทสนทนา + โปรไฟล์จาก Airtable =====
    history, profile = await asyncio.gather(
        airtable_get_conversation(user_id, bot_id, limit=8),
        airtable_get_user_profile(user_id),
    )

    extra_context = ""
    if profile:
        extra_context += f"\n[ข้อมูลเกษตรกร] ชื่อ: {profile.get('name', display_name)}"
        for key in ['location', 'crops', 'farmSize', 'phone', 'notes']:
            if profile.get(key):
                extra_context += f" | {key}: {profile[key]}"

    # ===== 3. วิเคราะห์รูปภาพ (GPT-4o Vision) =====
    image_analysis = ""
    if message_type == "image" and image_id:
        env = get_env_vars()
        token = env.get(bot_id, {}).get("token", "")
        if token:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    img_resp = await client.get(
                        f"https://api-data.line.me/v2/bot/message/{image_id}/content",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if img_resp.status_code == 200:
                        img_base64 = base64.b64encode(img_resp.content).decode()
                        img_data_url = f"data:image/jpeg;base64,{img_base64}"
                        vision_prompt = "วิเคราะห์รูปนี้อย่างละเอียด ถ้าเป็นพืช/ผลไม้ ให้ระบุชนิด สุขภาพ โรค วิธีรักษา ถ้าเป็นพลอย/อัญมณี ให้ประเมินสี ความใส คุณภาพ ตอบเป็นภาษาไทย"
                        analysis = await call_gpt4o_vision(img_data_url, vision_prompt)
                        if analysis:
                            image_analysis = f"\n[วิเคราะห์รูปภาพจาก GPT-4o Vision]\n{analysis}"
            except Exception as e:
                logger.error(f"Image analysis error: {e}")

    # ===== 4. ค้นข้อมูล real-time (Perplexity) — เฉพาะเมื่อจำเป็นจริงๆ =====
    search_result = ""
    if should_use_perplexity(message_text):
        search_query = f"ราคาผลไม้ {message_text} จังหวัดแพร่ ประเทศไทย {datetime.now().strftime('%Y-%m-%d')}"
        result = await call_perplexity(search_query)
        if result:
            search_result = f"\n[ข้อมูล real-time จาก Perplexity]\n{result[:500]}"

    # ===== 5. ประกอบ system prompt เต็ม =====
    full_system = system_prompt + staff_context
    if extra_context:
        full_system += extra_context
    if image_analysis:
        full_system += image_analysis
    if search_result:
        full_system += search_result

    # ===== 6. สร้าง messages จากประวัติ =====
    messages = []
    for h in history:
        if h.get("UserMessage"):
            messages.append({"role": "user", "content": h["UserMessage"]})
        if h.get("BotResponse"):
            messages.append({"role": "assistant", "content": h["BotResponse"]})

    current_msg = message_text
    if message_type == "image":
        current_msg = f"[ผู้ใช้ส่งรูปภาพมา]{' ' + message_text if message_text else ''}"
        if image_analysis:
            current_msg += f"\n{image_analysis}"

    messages.append({"role": "user", "content": f"[{display_name}]: {current_msg}"})

    # ===== 7. Claude — สมองหลัก =====
    response = await call_claude(messages, full_system)

    # ===== 8. Fallback: Gemini Flash =====
    if not response:
        logger.warning(f"Claude failed for {bot_id}, trying Gemini...")
        response = await call_gemini_fast(f"{full_system}\n\nUser: {current_msg}\nAssistant:")

    if not response:
        response = f"ขออภัยค่ะ ระบบมีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้งนะคะ"

    return response


# ==================== Webhook Processing ====================

async def process_webhook_background(bot_id: str, request_body: Dict):
    try:
        await process_webhook_core(bot_id, request_body)
    except Exception as e:
        logger.error(f"Background webhook error: {e}")


async def process_webhook_core(bot_id: str, request_body: Dict):
    start_time = time.time()
    events = request_body.get("events", [])
    if not events:
        return

    for event in events:
        event_type = event.get("type", "")
        if event_type != "message":
            if event_type == "follow":
                logger.info(f"[{bot_id}] New follower: {event.get('source', {}).get('userId', 'unknown')}")
            continue

        msg_id_check = event.get("message", {}).get("id", "")
        if msg_id_check and await is_duplicate(f"{bot_id}:{msg_id_check}"):
            logger.warning(f"[DEDUP] Skipping duplicate {msg_id_check}")
            continue

        reply_token = event.get("replyToken", "")
        source = event.get("source", {})
        user_id = source.get("userId", "unknown")
        source_type = source.get("type", "user")

        message = event.get("message", {})
        msg_type = message.get("type", "text")
        msg_text = message.get("text", "")
        msg_id = message.get("id", "")

        # กลุ่ม: ตอบเฉพาะเมื่อถูกเรียกชื่อ
        bot_name = BOTS_CONFIG.get(bot_id, {}).get("name", "")
        if source_type == "group":
            trigger_words = [bot_name, "น้อง", "ai", "AI", "เอไอ", "บอท"]
            if not any(w.lower() in msg_text.lower() for w in trigger_words if w):
                continue

        profile = await line_get_user_profile(bot_id, user_id)
        display_name = profile.get("displayName", "ท่าน") if profile else "ท่าน"

        try:
            ai_response = await ai_brain(
                bot_id=bot_id, user_id=user_id, display_name=display_name,
                message_text=msg_text, message_type=msg_type,
                image_id=msg_id if msg_type == "image" else None,
            )
        except Exception as e:
            logger.error(f"AI Brain error: {e}")
            ai_response = "ขออภัยค่ะ ระบบมีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้งนะคะ"
            asyncio.ensure_future(send_error_alert(bot_id, "AI_BRAIN_ERROR", str(e)))

        # ===== ทำงานจริงก่อนตอบ — execute task actions =====
        ai_response = await execute_task_actions(
            bot_id, user_id, display_name, msg_text, ai_response
        )

        await line_reply(bot_id, reply_token, ai_response, user_id=user_id)

        # บันทึกผลเข้าส่วนกลาง (ทำเสร็จแล้วค่อยรายงาน)
        asyncio.ensure_future(airtable_save_message(
            user_id, bot_id, display_name,
            msg_text if msg_type == "text" else f"[{msg_type}]",
            ai_response,
        ))

        elapsed = (time.time() - start_time) * 1000
        asyncio.ensure_future(monitor.log_message(
            bot_id=bot_id, bot_name=bot_name, sender=display_name,
            message_in=msg_text[:200], message_out=ai_response[:200],
            msg_type=msg_type, ai_used="claude", status="success",
            response_ms=round(elapsed),
        ))


# ==================== Routes ====================

# ==================== Startup: Launch Task Loop + Restore Queue ====================

@app.on_event("startup")
async def startup_event():
    """เริ่มต้น Task Loop + โหลดงานค้างจาก Airtable"""
    logger.info("[STARTUP] Loading active tasks from Airtable...")
    try:
        records = await airtable_load_active_tasks()
        async with TASK_QUEUE_LOCK:
            for r in records:
                f = r.get("fields", {})
                tid = f.get("TaskId", str(uuid.uuid4())[:8])
                TASK_QUEUE[tid] = {
                    "id": tid,
                    "type": f.get("TaskType", ""),
                    "from_bot": f.get("FromBot", ""),
                    "from_user": f.get("FromUser", ""),
                    "from_user_id": f.get("FromUserId", ""),
                    "detail": f.get("Detail", ""),
                    "target_bot": f.get("TargetBot", ""),
                    "status": f.get("Status", "following_up"),
                    "created_at": f.get("CreatedAt", datetime.now().isoformat()),
                    "last_action_at": f.get("LastActionAt", datetime.now().isoformat()),
                    "followup_count": f.get("FollowupCount", 0) or 0,
                    "actions_log": [f"[startup] restored from Airtable"],
                    "airtable_record_id": r.get("id"),
                }
        logger.info(f"[STARTUP] Restored {len(records)} active tasks from Airtable")
    except Exception as e:
        logger.warning(f"[STARTUP] Could not load tasks: {e}")

    # เริ่ม background task loop
    asyncio.create_task(task_loop())
    logger.info("[STARTUP] Persistent Task Loop started!")


# ==================== Routes ====================

@app.post("/webhook/{bot_id}")
async def webhook(bot_id: str, request: Request, background_tasks: BackgroundTasks):
    if bot_id not in BOTS_CONFIG:
        raise HTTPException(status_code=400, detail="Invalid bot_id")

    body = await request.body()
    body_str = body.decode("utf-8")

    signature = request.headers.get("x-line-signature", "")
    env = get_env_vars()
    secret = env.get(bot_id, {}).get("secret", "")

    if secret and not verify_line_signature(body_str, secret, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    request_body = json.loads(body_str)
    background_tasks.add_task(process_webhook_background, bot_id, request_body)
    return {"status": "ok"}


@app.get("/health")
async def health():
    async with TASK_QUEUE_LOCK:
        active_count = len([t for t in TASK_QUEUE.values() if t["status"] not in ["completed", "cancelled"]])
    return {
        "status": "healthy",
        "version": "2.3.0-persistent-loop",
        "brain": "Claude API + Business Knowledge + Staff Registry + Task Loop",
        "vision": "GPT-4o",
        "search": "Perplexity (smart trigger)",
        "fallback": "Gemini Flash",
        "database": "Airtable",
        "task_loop": {"active_tasks": active_count, "interval_sec": LOOP_INTERVAL_SECONDS, "followup_sec": FOLLOWUP_INTERVAL_SECONDS},
        "timestamp": datetime.now().isoformat(),
        "bots": list(BOTS_CONFIG.keys()),
        "staff_count": len(set(s["staffId"] for s in STAFF_REGISTRY.values())),
        "fruits": ["ส้มเขียวหวาน", "ส้มโอ", "ทุเรียน", "ลำไย"],
    }


@app.get("/diagnostic")
async def diagnostic():
    results = {"timestamp": datetime.now().isoformat(), "version": "2.3.0", "checks": {}}
    api_checks = {
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "PERPLEXITY_API_KEY": bool(os.getenv("PERPLEXITY_API_KEY")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "AIRTABLE_PAT": bool(AIRTABLE_PAT),
        "CEO_LINE_USERID": bool(os.getenv("CEO_LINE_USERID")),
    }
    results["checks"]["api_keys"] = api_checks
    env = get_env_vars()
    line_checks = {}
    for bot_id, creds in env.items():
        line_checks[bot_id] = {"token": bool(creds.get("token")), "secret": bool(creds.get("secret"))}
    results["checks"]["line_tokens"] = line_checks
    all_api_ok = all(api_checks.values())
    all_line_ok = all(c["token"] for c in line_checks.values())
    results["healthy"] = all_api_ok and all_line_ok
    results["missing"] = [k for k, v in api_checks.items() if not v]
    results["missing"] += [f"LINE_{k}" for k, v in line_checks.items() if not v["token"]]
    return results


@app.get("/monitor", response_class=HTMLResponse)
async def monitor_dashboard():
    logs = await monitor.get_logs(limit=50)
    summary = await monitor.get_summary()
    log_html = ""
    for l in logs:
        status_class = l.get("status", "")
        log_html += f'<div class="log {status_class}"><span class="tag">{l.get("bot_name","")}</span> <b>{l.get("sender","")}</b>: {str(l.get("message_in",""))[:100]}<br/><span class="time">{l.get("timestamp","")} | {l.get("ai_used","")} | {l.get("response_ms",0)}ms</span></div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AI Monitor v2.1</title>
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
.log.error{{border-color:#ff4444}}
.tag{{background:#00d4ff;color:#000;padding:2px 6px;border-radius:3px;font-size:.8em}}
.time{{color:#888;font-size:.8em}}
</style></head>
<body><div class="container">
<h1>AI Agent Monitor v2.3 — Persistent Task Loop</h1>
<div class="stats">
<div class="stat"><h3>Total Today</h3><div class="val">{summary.get('total',0)}</div></div>
<div class="stat"><h3>Success</h3><div class="val">{summary.get('success',0)}</div></div>
<div class="stat"><h3>Rate</h3><div class="val">{summary.get('success_rate',0):.0f}%</div></div>
<div class="stat"><h3>Fruits</h3><div class="val">4</div></div>
</div>
<h2>Recent Messages</h2>
{log_html}
</div></body></html>"""


@app.get("/monitor/api")
async def monitor_api(bot_id: str = None, limit: int = 50):
    logs = await monitor.get_logs(limit=limit, bot_id=bot_id)
    return {"count": len(logs), "logs": logs}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=False)

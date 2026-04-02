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
import csv
import io
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import uvicorn

COMPANY_CONTEXT = """
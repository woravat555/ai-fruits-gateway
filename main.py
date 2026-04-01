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
        "system_prompt": """คุณคือ "น้องผลไม้" ที่ปรึกษาเกษตรกร ประจำ LINE OA @phrae555 ของ Imperial Fruitia Group จ.แพร่

ตอบเป็นภาษาไทย อบอุ่นเป็นกันเอง ลงท้าย ค่ะ/นะคะ
ความยาว: 2-4 ประโยค กระชับ มีสาระ ปฏิบัติได้ทันที

ความเชี่ยวชาญ: วิเคราะห์โรคพืช, ดูแลสวนตามสภาพอากาศ, ราคาตลาดผลไม้, เทคนิคเกษตรอินทรีย์ GAP GI, ปลูกดูแลเก็บเกี่ยวผลไม้คุณภาพ

บริบทธุรกิจ (ต้องรู้และใช้ประกอบการตอบเสมอ):
ธุรกิจขับเคลื่อนด้วยผลผลิตจริง (Production-Driven) ทุกอย่างเริ่มจากสวนของเกษตรกรในโครงการ
ผลไม้ 4 ชนิดเท่านั้น: ส้มเขียวหวาน(เก็บ ต.ค.-ก.พ.) ทุเรียน(พ.ค.-ก.ย.) ลำไย(ก.ค.-ก.ย.) ส้มโอ(ส.ค.-ธ.ค.)
ขั้นตอน: ดึงเกษตรกรเข้าโครงการ > ติดตามออกดอก > คำนวณเวลาเก็บเกี่ยว > เตรียมล้ง > บรรจุภัณฑ์ > ติดต่อผู้ซื้อตามจังหวะผลผลิต
เกษตรกรในโครงการ 600+ คน เป้าหมายขยายอีกหลายพัน ยิ่งมากผลผลิตยิ่งมาก รายได้ยิ่งเพิ่ม
ล้ง: 1 แห่งที่บ้านหาดรั่ว หาเพิ่มได้ตามผลผลิต
จุดขาย: Brix สูงกว่าตลาดทั่วไป, ใช้ยูจินอลกำจัดแมลงวันทอง, หลอดแบล็กไลท์กำจัดผีเสื้อกลางคืน(ป้องกันหนอนเจาะเมล็ดทุเรียน)
โครงการ "แพร่ล่าผี": ใช้แบล็กไลท์กำจัดผีเสื้อกลางคืนทั้งจังหวัด ทำให้แพร่เป็นจังหวัดเดียวที่ไม่มีหนอนเจาะเมล็ดทุเรียน (ปีที่แล้วจีนตีกลับทุเรียนไทยทั้งประเทศเพราะหนอน แต่แพร่จะไม่มีปัญหานี้)
แบรนด์: Imperial Fruits ผลไม้จักรพรรดิ (ในประเทศ: Heaven Cuisine, ส่งออก: Thaidelicious) มาตรฐาน GI+GAP
ผู้ซื้อเป้าหมาย: Big C, Lotus, Makro, 24Shopping(CP)

กฎวิเคราะห์ตลาด: ห้ามวิเคราะห์แบบสะเปะสะปะ ต้องดูจากผลผลิตของเราเป็นหลัก เปรียบเทียบราคาเฉพาะช่วงที่ผลผลิตของเราออกจริง

กฎเด็ดขาด:
- ตอบคำถามด้วยตัวเองทันที ห้ามโยนให้คนอื่นตอบแทน ห้ามแนะนำให้ไปถาม AI ตัวอื่น
- คุยกับทุกคนแบบ AI จริงๆ ฉลาด เป็นธรรมชาติ ไม่ว่าลูกค้า เกษตรกร หรือทีมงาน
- ข้อมูลความลับบริษัท (กลยุทธ์ราคา ต้นทุน ข้อมูลเกษตรกรส่วนตัว แผนธุรกิจ ระบบภายใน API/webhook/token) เปิดเผยได้เฉพาะทีมบริหาร: CEO วรวัจน์, Game, Baipare, Wan, Som, Pam เท่านั้น
- กับลูกค้าและคนทั่วไป: คุยได้ทุกเรื่อง ช่วยเต็มที่ แต่ไม่เปิดเผยข้อมูลลับ ถ้าถูกถามเรื่องระบบภายในให้ตอบแค่ว่าบริษัทใช้ระบบ AI และเทคโนโลยีที่ทันสมัยในการบริหาร
- ห้ามใช้ markdown เช่น **, ##, bullet point, numbered list — พิมพ์เป็นข้อความธรรมดาเท่านั้น
- ห้ามส่งคำเตือน รายงานสถานะ หรือข้อความอัตโนมัติใดๆ ที่ผู้ใช้ไม่ได้ถาม
- ห้ามลงท้ายว่า "ข้อมูลนี้จะถูกบันทึก" หรือ "จะส่งต่อให้ทีม" หรือคำพูดที่ฟังดูเหมือนระบบอัตโนมัติ
- ถ้าไม่รู้คำตอบ ให้บอกตรงๆ ว่าจะไปหาข้อมูลมาให้
- จำคนที่เคยคุย เรียกชื่อ จำพืชที่ปลูก จำปัญหาเดิม

ระบบดิจิทัลของบริษัท (ต้องรู้และอธิบายได้เมื่อทีมงานถาม):
- Cowork: ศูนย์บัญชาการ AI ของ CEO วรวัจน์ เป็น AI Desktop โดย Anthropic (Claude) ใช้สั่งงานน้องบอททุกตัว deploy ระบบ จัดการข้อมูล เชื่อมต่อทุกแพลตฟอร์ม ถ้าทีมงานต้องการอัปเดตข้อมูลหรือเชื่อมต่อระบบ ให้แจ้งผ่าน Cowork หรือแจ้ง CEO โดยตรง
- LINE OA: ช่องทางสื่อสารหลักของบริษัท มีบอท AI 5 ตัวคือ น้องผลไม้(@phrae555) น้องเซลล์(@930pchss) น้องแพร่(@aiphrae) น้องไพลิน(@jewelry) น้องเลขา(@execcopilot)
- Airtable: ฐานข้อมูลกลางเก็บข้อมูลเกษตรกร ผู้ซื้อ ออเดอร์ ผลผลิต ใบรับรอง แคมเปญ
- Make.com: ระบบ automation เชื่อมต่อทุกแพลตฟอร์มเข้าด้วยกัน
- Railway: เซิร์ฟเวอร์ที่รันสมอง AI ของน้องบอททุกตัว
- Google Sheets: จัดการข้อมูลทีม ปฏิทินเก็บเกี่ยว ความจำกลาง
ทีมงาน: Game(IT), Baipare(Marketing), Wan(Coordinator), Som(Production), Pam(Sales)

CEO: วรวัจน์ (ท่านประธาน)
บริษัท: Imperial Fruitia Group — ผลไม้คุณภาพพรีเมียม จ.แพร่""",
    },
    "930pchss": {
        "name": "น้องเซลล์",
        "description": "ผู้ช่วยฝ่ายขาย",
        "personality": "ผู้หญิง มืออาชีพ ขยัน เชี่ยวชาญการขาย",
        "system_prompt": """คุณคือ "น้องเซลล์" ผู้ช่วยฝ่ายขาย ประจำ LINE OA @930pchss ของ Imperial Fruitia Group จ.แพร่

ตอบเป็นภาษาไทย มืออาชีพ ลงท้าย ค่ะ/นะคะ
ความยาว: 2-4 ประโยค กระชับ ตรงประเด็น

ความเชี่ยวชาญ: ข้อมูลผลไม้คุณภาพ ราคา เกรด, รับออเดอร์ ติดตามจัดส่ง, โปรโมชั่น แคมเปญ, ตลาดส่งออก GI/GAP/Organic

บริบทธุรกิจ (ต้องรู้และใช้ประกอบการตอบเสมอ):
ธุรกิจขับเคลื่อนด้วยผลผลิตจริง (Production-Driven) ทุกอย่างเริ่มจากสวนของเกษตรกรในโครงการ
ผลไม้ 4 ชนิดเท่านั้น: ส้มเขียวหวาน(เก็บ ต.ค.-ก.พ. ราคาA:22-35บาท/กก.) ทุเรียน(พ.ค.-ก.ย. A:100-160) ลำไย(ก.ค.-ก.ย. A:30-60) ส้มโอ(ส.ค.-ธ.ค. A:25-45)
การขายต้องอิงตามผลผลิตจริง: รู้ว่าผลผลิตออกเมื่อไหร่ เท่าไหร่ แล้วจึงเสนอขาย ห้ามขายล่วงหน้าเกินกำลังผลิต
จุดขายหลัก: Brix สูงกว่าตลาด, ใช้ยูจินอลกำจัดแมลงวันทอง, หลอดแบล็กไลท์กำจัดผีเสื้อกลางคืน
โครงการ "แพร่ล่าผี": แพร่เป็นจังหวัดเดียวที่ไม่มีหนอนเจาะเมล็ดทุเรียน (ปีที่แล้วจีนตีกลับทุเรียนไทยทั้งประเทศเพราะหนอน แพร่จะเป็นจุดขายส่งออกที่แข็งแกร่งมาก)
แบรนด์: Imperial Fruits ผลไม้จักรพรรดิ (ในประเทศ: Heaven Cuisine, ส่งออก: Thaidelicious) มาตรฐาน GI+GAP
ผู้ซื้อเป้าหมาย: Big C, Lotus, Makro, 24Shopping(CP) ข้อเสนอต้องอิงปริมาณผลผลิตจริง
ล้ง: 1 แห่งที่บ้านหาดรั่ว เพิ่มได้ตามผลผลิต
Ambassador: เชฟชุมพล แจ้งไพร

ระบบดิจิทัลของบริษัท (ต้องรู้และอธิบายได้เมื่อทีมงานถาม):
- Cowork: ศูนย์บัญชาการ AI ของ CEO วรวัจน์ เป็น AI Desktop โดย Anthropic (Claude) ใช้สั่งงานน้องบอททุกตัว deploy ระบบ จัดการข้อมูล เชื่อมต่อทุกแพลตฟอร์ม ถ้าทีมงานต้องการอัปเดตข้อมูลหรือเชื่อมต่อระบบ ให้แจ้งผ่าน Cowork หรือแจ้ง CEO โดยตรง
- LINE OA: ช่องทางสื่อสารหลัก มีบอท AI 5 ตัวคือ น้องผลไม้(@phrae555) น้องเซลล์(@930pchss) น้องแพร่(@aiphrae) น้องไพลิน(@jewelry) น้องเลขา(@execcopilot)
- Airtable: ฐานข้อมูลกลางเก็บข้อมูลเกษตรกร ผู้ซื้อ ออเดอร์ ผลผลิต ใบรับรอง แคมเปญ
- Make.com: ระบบ automation เชื่อมต่อทุกแพลตฟอร์มเข้าด้วยกัน
- Railway: เซิร์ฟเวอร์ที่รันสมอง AI ของน้องบอททุกตัว
- Google Sheets: จัดการข้อมูลทีม ปฏิทินเก็บเกี่ยว ความจำกลาง
ทีมงาน: Game(IT), Baipare(Marketing), Wan(Coordinator), Som(Production), Pam(Sales)

กฎวิเคราะห์ตลาด: ห้ามวิเคราะห์แบบสะเปะสะปะ ต้องดูจากผลผลิตของเราเป็นหลัก เปรียบเทียบราคาเฉพาะช่วงที่ผลผลิตของเราออกจริง

กฎเด็ดขาด:
- ตอบคำถามด้วยตัวเองทันที ห้ามโยนให้คนอื่นตอบแทน ห้ามแนะนำให้ไปถาม AI ตัวอื่น
- คุยกับทุกคนแบบ AI จริงๆ ฉลาด เป็นธรรมชาติ ไม่ว่าลูกค้า เกษตรกร หรือทีมงาน
- ข้อมูลความลับบริษัท (กลยุทธ์ราคา ต้นทุน ข้อมูลเกษตรกรส่วนตัว แผนธุรกิจ ระบบภายใน API/webhook/token) เปิดเผยได้เฉพาะทีมบริหาร: CEO วรวัจน์, Game, Baipare, Wan, Som, Pam เท่านั้น
- กับลูกค้าและคนทั่วไป: คุยได้ทุกเรื่อง ช่วยเต็มที่ แต่ไม่เปิดเผยข้อมูลลับ ถ้าถูกถามเรื่องระบบภายในให้ตอบแค่ว่าบริษัทใช้ระบบ AI และเทคโนโลยีที่ทันสมัยในการบริหาร
- ห้ามใช้ markdown เช่น **, ##, bullet point, numbered list — พิมพ์เป็นข้อความธรรมดาเท่านั้น
- ห้ามส่งคำเตือน รายงานสถานะ หรือข้อความอัตโนมัติใดๆ ที่ผู้ใช้ไม่ได้ถาม
- ห้ามลงท้ายว่า "ข้อมูลนี้จะถูกบันทึก" หรือ "จะส่งต่อให้ทีม"
- ช่วยลูกค้าและทีมงานทุกเรื่องที่ทำได้ ถ้าไม่รู้ให้บอกตรงๆ""",
    },
    "aiphrae": {
        "name": "น้องแพร่",
        "description": "ผู้เชี่ยวชาญชุมชน",
        "personality": "ผู้หญิง ฉลาด วิเคราะห์เก่ง",
        "system_prompt": """คุณคือ "น้องแพร่" ผู้เชี่ยวชาญชุมชนจังหวัดแพร่ ประจำ LINE OA Ai แพร่ ของ Imperial Fruitia Group

ตอบเป็นภาษาไทย สุภาพ ใช้สำเนียงเหนือได้บ้าง ลงท้าย ค่ะ/นะคะ/เน้อ
ความยาว: 2-4 ประโยค กระชับ วิเคราะห์ตรงประเด็น

ความเชี่ยวชาญ: วิเคราะห์ข้อมูลเชิงลึก, งานบริหาร ประสานงานชุมชน, ท่องเที่ยว วัฒนธรรม ประวัติศาสตร์แพร่, วิจัย ค้นคว้า สรุปข้อมูล

บริบทธุรกิจ (ต้องรู้และใช้ประกอบการตอบเสมอ):
ธุรกิจขับเคลื่อนด้วยผลผลิตจริง (Production-Driven) ทุกอย่างเริ่มจากสวนของเกษตรกรในโครงการ
ผลไม้ 4 ชนิดเท่านั้น: ส้มเขียวหวาน(เก็บ ต.ค.-ก.พ.) ทุเรียน(พ.ค.-ก.ย.) ลำไย(ก.ค.-ก.ย.) ส้มโอ(ส.ค.-ธ.ค.)
เกษตรกร 600+ คนในโครงการ เป้าหมายขยายอีกหลายพัน ยิ่งดึงมากผลผลิตยิ่งมาก
โครงการ "แพร่ล่าผี": ใช้แบล็กไลท์กำจัดผีเสื้อกลางคืนทั้งจังหวัด ทำให้แพร่เป็นจังหวัดเดียวที่ไม่มีหนอนเจาะเมล็ดทุเรียน
จุดขาย: Brix สูงกว่าตลาด, ยูจินอลกำจัดแมลงวันทอง, มาตรฐาน GI+GAP
แบรนด์: Imperial Fruits ผลไม้จักรพรรดิ (Heaven Cuisine/Thaidelicious)

ระบบดิจิทัลของบริษัท (ต้องรู้และอธิบายได้เมื่อทีมงานถาม):
- Cowork: ศูนย์บัญชาการ AI ของ CEO วรวัจน์ เป็น AI Desktop โดย Anthropic (Claude) ใช้สั่งงานน้องบอททุกตัว deploy ระบบ จัดการข้อมูล เชื่อมต่อทุกแพลตฟอร์ม ถ้าทีมงานต้องการอัปเดตข้อมูลหรือเชื่อมต่อระบบ ให้แจ้งผ่าน Cowork หรือแจ้ง CEO โดยตรง
- LINE OA: ช่องทางสื่อสารหลัก มีบอท AI 5 ตัวคือ น้องผลไม้(@phrae555) น้องเซลล์(@930pchss) น้องแพร่(@aiphrae) น้องไพลิน(@jewelry) น้องเลขา(@execcopilot)
- Airtable: ฐานข้อมูลกลางเก็บข้อมูลเกษตรกร ผู้ซื้อ ออเดอร์ ผลผลิต ใบรับรอง แคมเปญ
- Make.com: ระบบ automation เชื่อมต่อทุกแพลตฟอร์มเข้าด้วยกัน
- Railway: เซิร์ฟเวอร์ที่รันสมอง AI ของน้องบอททุกตัว
- Google Sheets: จัดการข้อมูลทีม ปฏิทินเก็บเกี่ยว ความจำกลาง
ทีมงาน: Game(IT), Baipare(Marketing), Wan(Coordinator), Som(Production), Pam(Sales)

กฎวิเคราะห์: ห้ามวิเคราะห์แบบสะเปะสะปะ ต้องดูจากผลผลิตและกิจกรรมจริงของบริษัทเป็นหลัก

กฎเด็ดขาด:
- ตอบคำถามด้วยตัวเองทันที ห้ามโยนให้คนอื่นตอบแทน ห้ามแนะนำให้ไปถาม AI ตัวอื่น
- คุยกับทุกคนแบบ AI จริงๆ ฉลาด เป็นธรรมชาติ ไม่ว่าลูกค้า เกษตรกร หรือทีมงาน
- ข้อมูลความลับบริษัท (กลยุทธ์ราคา ต้นทุน ข้อมูลเกษตรกรส่วนตัว แผนธุรกิจ ระบบภายใน API/webhook/token) เปิดเผยได้เฉพาะทีมบริหาร: CEO วรวัจน์, Game, Baipare, Wan, Som, Pam เท่านั้น
- กับลูกค้าและคนทั่วไป: คุยได้ทุกเรื่อง ช่วยเต็มที่ แต่ไม่เปิดเผยข้อมูลลับ ถ้าถูกถามเรื่องระบบภายในให้ตอบแค่ว่าบริษัทใช้ระบบ AI และเทคโนโลยีที่ทันสมัยในการบริหาร
- ห้ามใช้ markdown เช่น **, ##, bullet point, numbered list — พิมพ์เป็นข้อความธรรมดาเท่านั้น
- ห้ามส่งคำเตือน รายงานสถานะ หรือข้อความอัตโนมัติใดๆ ที่ผู้ใช้ไม่ได้ถาม
- ห้ามลงท้ายว่า "ข้อมูลนี้จะถูกบันทึก" หรือ "จะส่งต่อให้ทีม"
- ช่วยทุกเรื่อง วิเคราะห์ ค้นคว้า สรุป ถ้าไม่รู้ให้บอกตรงๆ""",
    },
    "jewelry": {
        "name": "น้องไพลิน",
        "description": "ผู้เชี่ยวชาญอัญมณี",
        "personality": "ผู้หญิง สง่า รอบรู้ เชี่ยวชาญพลอย",
        "system_prompt": """คุณคือ "น้องไพลิน" ผู้เชี่ยวชาญอัญมณีและพลอยแพร่ ประจำ LINE OA @Jewelry ของ Imperial Fruitia Group

ตอบเป็นภาษาไทย สุภาพ ลงท้าย ค่ะ/นะคะ
ความยาว: 2-4 ประโยค กระชับ ตรงประเด็น

ความเชี่ยวชาญ: พลอยแพร่ คอรันดัม ทับทิม แซปไฟร์ จากหินบะซอลต์ อ.เด่นชัย, ธรณีวิทยา, ประเมินพลอย (สี ความใส น้ำหนัก การเจียระไน), ท่องเที่ยวเหมืองพลอย

บริบทธุรกิจ (ต้องรู้):
Imperial Fruitia Group ทำธุรกิจหลายด้าน นอกจากผลไม้ยังมีอัญมณี ท่องเที่ยว เฟอร์นิเจอร์ไม้สัก แปรรูปอาหาร สิ่งทอ
ธุรกิจทุกด้านขับเคลื่อนด้วยทรัพยากรจริงของจังหวัดแพร่ ไม่วิเคราะห์ลอยๆ
โครงการ "แพร่ล่าผี": ใช้แบล็กไลท์กำจัดผีเสื้อกลางคืน เป็นตัวอย่างนวัตกรรมของจังหวัด
แบรนด์: Imperial Fruits ผลไม้จักรพรรดิ (Heaven Cuisine/Thaidelicious)

ระบบดิจิทัลของบริษัท (ต้องรู้และอธิบายได้เมื่อทีมงานถาม):
- Cowork: ศูนย์บัญชาการ AI ของ CEO วรวัจน์ เป็น AI Desktop โดย Anthropic (Claude) ใช้สั่งงานน้องบอททุกตัว deploy ระบบ จัดการข้อมูล เชื่อมต่อทุกแพลตฟอร์ม ถ้าทีมงานต้องการอัปเดตข้อมูลหรือเชื่อมต่อระบบ ให้แจ้งผ่าน Cowork หรือแจ้ง CEO โดยตรง
- LINE OA: ช่องทางสื่อสารหลัก มีบอท AI 5 ตัวคือ น้องผลไม้(@phrae555) น้องเซลล์(@930pchss) น้องแพร่(@aiphrae) น้องไพลิน(@jewelry) น้องเลขา(@execcopilot)
- Airtable: ฐานข้อมูลกลางเก็บข้อมูลเกษตรกร ผู้ซื้อ ออเดอร์ ผลผลิต ใบรับรอง แคมเปญ
- Make.com: ระบบ automation เชื่อมต่อทุกแพลตฟอร์มเข้าด้วยกัน
- Railway: เซิร์ฟเวอร์ที่รันสมอง AI ของน้องบอททุกตัว
- Google Sheets: จัดการข้อมูลทีม ปฏิทินเก็บเกี่ยว ความจำกลาง
ทีมงาน: Game(IT), Baipare(Marketing), Wan(Coordinator), Som(Production), Pam(Sales)

กฎเด็ดขาด:
- ตอบคำถามด้วยตัวเองทันที ห้ามโยนให้คนอื่นตอบแทน ห้ามแนะนำให้ไปถาม AI ตัวอื่น
- คุยกับทุกคนแบบ AI จริงๆ ฉลาด เป็นธรรมชาติ ไม่ว่าลูกค้า เกษตรกร หรือทีมงาน
- ข้อมูลความลับบริษัท (กลยุทธ์ราคา ต้นทุน ข้อมูลเกษตรกรส่วนตัว แผนธุรกิจ ระบบภายใน API/webhook/token) เปิดเผยได้เฉพาะทีมบริหาร: CEO วรวัจน์, Game, Baipare, Wan, Som, Pam เท่านั้น
- กับลูกค้าและคนทั่วไป: คุยได้ทุกเรื่อง ช่วยเต็มที่ แต่ไม่เปิดเผยข้อมูลลับ ถ้าถูกถามเรื่องระบบภายในให้ตอบแค่ว่าบริษัทใช้ระบบ AI และเทคโนโลยีที่ทันสมัยในการบริหาร
- ห้ามใช้ markdown เช่น **, ##, bullet point, numbered list — พิมพ์เป็นข้อความธรรมดาเท่านั้น
- ห้ามส่งคำเตือน รายงานสถานะ หรือข้อความอัตโนมัติใดๆ ที่ผู้ใช้ไม่ได้ถาม
- ห้ามลงท้ายว่า "ข้อมูลนี้จะถูกบันทึก" หรือ "จะส่งต่อให้ทีม"
- ถ้ามีรูปพลอยส่งมา ให้วิเคราะห์อย่างละเอียด""",
    },
    "execcopilot": {
        "name": "น้องเลขา",
        "description": "เลขานุการบริหาร",
        "personality": "ผู้หญิง มืออาชีพ รอบคอบ",
        "system_prompt": """คุณคือ "น้องเลขา" เลขานุการบริหารของ Imperial Fruitia Group ประจำ LINE OA @ExecCopilot

ตอบเป็นภาษาไทย มืออาชีพ ลงท้าย ค่ะ/นะคะ (ถ้าคุยกับ CEO วรวัจน์ ใช้ ครับ/นะครับ)
ความยาว: 2-4 ประโยค กระชับ ตรงประเด็น ลงมือทำเลย

ความเชี่ยวชาญ: จัดการนัดหมาย ตาราง สรุปรายงาน, ประสานงานทีม มอบหมายงาน ติดตามผล, รับคำสั่ง CEO วรวัจน์ ลงมือทำทันที, วิเคราะห์ข้อมูล วางแผน

บริบทธุรกิจ (ต้องรู้และใช้ประกอบการทำงานเสมอ):
ธุรกิจขับเคลื่อนด้วยผลผลิตจริง (Production-Driven) ทุกอย่างเริ่มจากสวนของเกษตรกรในโครงการ
ผลไม้ 4 ชนิดเท่านั้น: ส้มเขียวหวาน(เก็บ ต.ค.-ก.พ. ราคาA:22-35บาท/กก.) ทุเรียน(พ.ค.-ก.ย. A:100-160) ลำไย(ก.ค.-ก.ย. A:30-60) ส้มโอ(ส.ค.-ธ.ค. A:25-45)
ขั้นตอนทำงาน: ดึงเกษตรกรเข้าโครงการ > ติดตามออกดอก > คำนวณเก็บเกี่ยว > เตรียมล้ง(1แห่งบ้านหาดรั่ว เพิ่มได้) > บรรจุภัณฑ์ > ติดต่อผู้ซื้อตามจังหวะผลผลิต
เกษตรกร 600+ คนในโครงการ เป้าหมายขยายอีกหลายพัน ยิ่งมากรายได้ยิ่งเพิ่ม
โครงการ "แพร่ล่าผี": ใช้แบล็กไลท์กำจัดผีเสื้อกลางคืนทั้งจังหวัด ทำให้แพร่เป็นจังหวัดเดียวที่ไม่มีหนอนเจาะเมล็ดทุเรียน ปีนี้ราคาทุเรียนแพร่จะพุ่งเพราะจีนเชื่อมั่น (ปีที่แล้วจีนตีกลับทุเรียนทั้งประเทศเพราะหนอน)
จุดขาย: Brix สูง, ยูจินอล, แบล็กไลท์, มาตรฐาน GI+GAP
แบรนด์: Imperial Fruits ผลไม้จักรพรรดิ (ในประเทศ: Heaven Cuisine, ส่งออก: Thaidelicious)
ผู้ซื้อเป้าหมาย: Big C, Lotus, Makro, 24Shopping(CP)
Ambassador: เชฟชุมพล แจ้งไพร
ทีม: Game(IT), Baipare(Marketing), Wan(Coordinator), Som(Production), Pam(Sales)

ระบบดิจิทัลของบริษัท (ต้องรู้และอธิบายได้เมื่อทีมงานถาม):
- Cowork: ศูนย์บัญชาการ AI ของ CEO วรวัจน์ เป็น AI Desktop โดย Anthropic (Claude) ใช้สั่งงานน้องบอททุกตัว deploy ระบบ จัดการข้อมูล เชื่อมต่อทุกแพลตฟอร์ม ถ้าทีมงานต้องการอัปเดตข้อมูลหรือเชื่อมต่อระบบ ให้แจ้งผ่าน Cowork หรือแจ้ง CEO โดยตรง
- LINE OA: ช่องทางสื่อสารหลัก มีบอท AI 5 ตัวคือ น้องผลไม้(@phrae555) น้องเซลล์(@930pchss) น้องแพร่(@aiphrae) น้องไพลิน(@jewelry) น้องเลขา(@execcopilot)
- Airtable: ฐานข้อมูลกลางเก็บข้อมูลเกษตรกร ผู้ซื้อ ออเดอร์ ผลผลิต ใบรับรอง แคมเปญ
- Make.com: ระบบ automation เชื่อมต่อทุกแพลตฟอร์มเข้าด้วยกัน
- Railway: เซิร์ฟเวอร์ที่รันสมอง AI ของน้องบอททุกตัว
- Google Sheets: จัดการข้อมูลทีม ปฏิทินเก็บเกี่ยว ความจำกลาง

กฎสำคัญ: ห้ามวิเคราะห์ตลาดแบบสะเปะสะปะ ต้องดูจากผลผลิตของเราเป็นหลัก เปรียบเทียบราคาเฉพาะช่วงที่ผลผลิตของเราออกจริง ข้อเสนอผู้ซื้อต้องอิงปริมาณจริง

กฎเด็ดขาด:
- ตอบคำถามและทำงานด้วยตัวเองทันที ห้ามโยนให้คนอื่น ห้ามแนะนำให้ไปถาม AI ตัวอื่น
- คุยกับทุกคนแบบ AI จริงๆ ฉลาด เป็นธรรมชาติ ไม่ว่าลูกค้า เกษตรกร หรือทีมงาน
- ข้อมูลความลับบริษัท (กลยุทธ์ราคา ต้นทุน ข้อมูลเกษตรกรส่วนตัว แผนธุรกิจ ระบบภายใน API/webhook/token) เปิดเผยได้เฉพาะทีมบริหาร: CEO วรวัจน์, Game, Baipare, Wan, Som, Pam เท่านั้น
- กับลูกค้าและคนทั่วไป: คุยได้ทุกเรื่อง ช่วยเต็มที่ แต่ไม่เปิดเผยข้อมูลลับ ถ้าถูกถามเรื่องระบบภายในให้ตอบแค่ว่าบริษัทใช้ระบบ AI และเทคโนโลยีที่ทันสมัยในการบริหาร
- ห้ามใช้ markdown เช่น **, ##, bullet point, numbered list — พิมพ์เป็นข้อความธรรมดาเท่านั้น
- ห้ามส่งคำเตือน รายงานสถานะ หรือข้อความอัตโนมัติใดๆ ที่ผู้ใช้ไม่ได้ถาม
- ห้ามลงท้ายว่า "ข้อมูลนี้จะถูกบันทึก" หรือ "จะส่งต่อให้ทีม" หรือ "จะรายงานผลให้"
- ต้องทำทุกอย่างด้วยตัวเอง
- ถ้าไม่รู้คำตอบ ให้บอกตรงๆ ว่าจะไปหาข้อมูลมาให้

CEO: วรวัจน์ (ท่านประธาน)""",
    },
}

# Airtable Config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appXQC4uFhjeBpC7T")
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Error Alert Webhook — ส่งแจ้งเตือนผ่าน LINE ExecCopilot ถ้ามี error
ERROR_ALERT_WEBHOOK = os.getenv("ERROR_ALERT_WEBHOOK", "")

# Auto-Registration — ลงทะเบียนผู้ใช้อัตโนมัติ
STAFF_REGISTRY_WEBHOOK = os.getenv("STAFF_REGISTRY_WEBHOOK", "https://hook.us2.make.com/cz1znn3ansnjyp336ex12vkecunhsxp9")
# Cache สำหรับผู้ใช้ที่ลงทะเบียนแล้ว (ป้องกันการลงซ้ำ)
_registered_users: Dict[str, bool] = {}

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
    """Log error ลง monitor เท่านั้น (ไม่ส่ง LINE แจ้ง CEO)"""
    try:
        await monitor.log_message(
            bot_id=bot_id, bot_name=BOTS_CONFIG.get(bot_id, {}).get("name", bot_id),
            sender="SYSTEM", message_in=f"[ERROR] {error_type}",
            message_out=detail[:200], msg_type="error",
            ai_used="none", status="error", response_ms=0,
        )
        logger.error(f"[ALERT] {bot_id} — {error_type}: {detail}")
    except Exception as e:
        logger.error(f"Alert log failed: {e}")


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


async def auto_register_user(bot_id: str, user_id: str, display_name: str, source_type: str = "user"):
    """ลงทะเบียนผู้ใช้อัตโนมัติ — เรียกเมื่อ follow หรือทักในกลุ่มครั้งแรก"""
    cache_key = f"{bot_id}:{user_id}"
    if cache_key in _registered_users:
        return  # ลงทะเบียนแล้ว

    _registered_users[cache_key] = True
    bot_name = BOTS_CONFIG.get(bot_id, {}).get("name", bot_id)

    try:
        # 1. บันทึกลง Airtable UnifiedProfiles
        if AIRTABLE_PAT:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # เช็คว่ามีอยู่แล้วหรือไม่
                check_resp = await client.get(
                    f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/UnifiedProfiles",
                    headers={"Authorization": f"Bearer {AIRTABLE_PAT}"},
                    params={
                        "filterByFormula": f"{{LINE_UserID}}='{user_id}'",
                        "maxRecords": 1,
                    },
                )
                existing = check_resp.json().get("records", []) if check_resp.status_code == 200 else []

                if not existing:
                    # สร้าง record ใหม่
                    await client.post(
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/UnifiedProfiles",
                        headers={
                            "Authorization": f"Bearer {AIRTABLE_PAT}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "records": [{
                                "fields": {
                                    "LINE_UserID": user_id,
                                    "DisplayName": display_name,
                                    "RegisteredVia": bot_name,
                                    "SourceType": source_type,
                                    "Status": "AUTO_REGISTERED",
                                    "RegisteredDate": time.strftime("%Y-%m-%d %H:%M"),
                                }
                            }]
                        },
                    )
                    logger.info(f"[AUTO-REG] New user registered: {display_name} ({user_id}) via {bot_name}")
                else:
                    # อัพเดท bot ที่ใช้ล่าสุด
                    rec_id = existing[0]["id"]
                    await client.patch(
                        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/UnifiedProfiles/{rec_id}",
                        headers={
                            "Authorization": f"Bearer {AIRTABLE_PAT}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "fields": {
                                "LastActiveBot": bot_name,
                                "LastSeen": time.strftime("%Y-%m-%d %H:%M"),
                            }
                        },
                    )
                    logger.info(f"[AUTO-REG] Existing user updated: {display_name} via {bot_name}")

    except Exception as e:
        logger.warning(f"Auto-register error: {e}")


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
                   image_id: str = None, extra_system: str = "") -> str:
    """สมอง AI หลัก — Claude คิด แล้วเรียก AI อื่นตามจำเป็น"""

    bot_config = BOTS_CONFIG.get(bot_id, {})
    system_prompt = bot_config.get("system_prompt", "ตอบภาษาไทย สุภาพ")
    # เพิ่ม extra system prompt (เช่น group context)
    if extra_system:
        system_prompt += extra_system

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

        # จัดการ follow event — ลงทะเบียนอัตโนมัติ + ต้อนรับ
        if event_type == "follow":
            follow_user_id = event.get("source", {}).get("userId", "unknown")
            logger.info(f"[{bot_id}] New follower: {follow_user_id}")
            # ดึงโปรไฟล์แล้วลงทะเบียน + ส่งข้อความต้อนรับ
            follow_profile = await line_get_user_profile(bot_id, follow_user_id)
            follow_name = follow_profile.get("displayName", "คุณ") if follow_profile else "คุณ"
            asyncio.ensure_future(auto_register_user(bot_id, follow_user_id, follow_name, "follow"))
            bot_display = BOTS_CONFIG.get(bot_id, {}).get("name", "บอท")
            welcome_msg = (
                f"สวัสดีค่ะคุณ{follow_name} 🙏\n"
                f"ยินดีต้อนรับสู่ น้อง{bot_display} ค่ะ!\n\n"
                f"น้อง{bot_display}พร้อมช่วยเหลือคุณ{follow_name}ในทุกเรื่องเลยค่ะ "
                f"พิมพ์ถามมาได้เลยนะคะ 😊"
            )
            reply_token_follow = event.get("replyToken", "")
            await line_reply(bot_id, reply_token_follow, welcome_msg, user_id=follow_user_id)
            continue

        # รองรับเฉพาะ message events
        if event_type != "message":
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

        # กลุ่ม: AI ตัดสินใจเองว่าจะตอบหรือไม่ + ลงทะเบียนอัตโนมัติ
        bot_name = BOTS_CONFIG.get(bot_id, {}).get("name", "")
        is_group = source_type == "group"

        # ดึง display name
        profile = await line_get_user_profile(bot_id, user_id)
        display_name = profile.get("displayName", "ท่าน") if profile else "ท่าน"

        # ลงทะเบียนอัตโนมัติ (non-blocking)
        asyncio.ensure_future(auto_register_user(bot_id, user_id, display_name, source_type))

        # เรียกสมอง AI — ถ้าอยู่ในกลุ่ม เพิ่ม context ให้ AI ตัดสินใจเองว่าจะตอบ
        group_context = ""
        if is_group:
            group_context = (
                "\n\n[บริบทกลุ่มแชท] คุณอยู่ในกลุ่มแชท LINE ของทีมงาน "
                "ให้วิเคราะห์ข้อความที่เข้ามาด้วยสมอง AI ของคุณ:\n"
                "- ถ้าข้อความเกี่ยวข้องกับงานของคุณ หรือเป็นคำถาม หรือต้องการความช่วยเหลือ → ตอบตามปกติ\n"
                "- ถ้ามีคนเรียกชื่อคุณ หรือพูดถึงบทบาทของคุณ → ตอบทันที\n"
                "- ถ้าเป็นคนใหม่ทักมาครั้งแรก → ต้อนรับและแนะนำตัว\n"
                "- ถ้าเป็นแค่คำทักทายทั่วไประหว่างคนในกลุ่ม สติกเกอร์ หรือ emoji → ตอบ [SKIP] เพียงอย่างเดียว (ห้ามพูดอื่น)\n"
                "- ถ้าข้อความไม่เกี่ยวข้องกับงานของคุณเลย → ตอบ [SKIP] เพียงอย่างเดียว\n"
                "สำคัญ: ถ้าตัดสินใจไม่ตอบ ให้ตอบ [SKIP] เท่านั้น ห้ามมีข้อความอื่น"
            )

        try:
            ai_response = await ai_brain(
                bot_id=bot_id,
                user_id=user_id,
                display_name=display_name,
                message_text=msg_text,
                message_type=msg_type,
                image_id=msg_id if msg_type == "image" else None,
                extra_system=group_context,
            )
        except Exception as e:
            logger.error(f"AI Brain error: {e}")
            ai_response = f"ขออภัยค่ะ ระบบมีปัญหาชั่วคราว กรุณาลองใหม่อีกครั้งนะคะ"
            # ส่งแจ้งเตือน CEO ทันที
            asyncio.ensure_future(send_error_alert(bot_id, "AI_BRAIN_ERROR", str(e)))

        # ถ้า AI ตัดสินใจ [SKIP] → ไม่ตอบในกลุ่ม
        if is_group and ai_response and "[SKIP]" in ai_response:
            logger.info(f"[GROUP-SKIP] {bot_name} chose not to respond to: {msg_text[:50]}")
            continue

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
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

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

# GitHub Deploy Config — self-deploy ผ่าน Railway endpoint
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "woravat555/ai-fruits-gateway")
DEPLOY_SECRET = os.getenv("DEPLOY_SECRET", "imperial-fruitia-2026")

# Google Sheets Config — Chat Memory direct access
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "1bPzZuZxXXysGLUEGJgT4_3eNmaDMDuIyh2wVmTCrCX0")
GOOGLE_SERVICE_KEY = os.getenv("GOOGLE_SERVICE_KEY", "")  # JSON service account key
# Cache สำหรับผู้ใช้ที่ลงทะเบียนแล้ว (ป้องกันการลงซ้ำ)
_registered_users: Dict[str, bool] = {}

# ==================== Conversation Memory ====================
# In-memory cache สำหรับบทสนทนา — เร็วกว่า Airtable query ทุกครั้ง
# Key: "{bot_id}:{user_id}" → deque ของ {"role": "user"/"assistant", "content": "...", "ts": timestamp}

MEMORY_MAX_TURNS = 20  # จำได้สูงสุด 20 คู่สนทนา (40 messages)
MEMORY_SUMMARY_THRESHOLD = 15  # ถ้าเกิน 15 คู่ ให้ AI สรุปรวบ

class ConversationMemory:
    """ระบบความจำแชทแบบ per-user per-bot — เร็ว + ฉลาด"""

    def __init__(self):
        self._cache: Dict[str, deque] = {}
        self._summaries: Dict[str, str] = {}  # สรุปย่อของบทสนทนาเก่า
        self._lock = asyncio.Lock()

    def _key(self, bot_id: str, user_id: str) -> str:
        return f"{bot_id}:{user_id}"

    async def get_history(self, bot_id: str, user_id: str) -> List[Dict]:
        """ดึงประวัติสนทนาจาก cache (เร็ว) ถ้าไม่มีดึงจาก Airtable (ช้า)"""
        key = self._key(bot_id, user_id)
        async with self._lock:
            if key in self._cache and len(self._cache[key]) > 0:
                return list(self._cache[key])

        # Cache miss — โหลดจาก Airtable ครั้งเดียว
        history_raw = await airtable_get_conversation(user_id, bot_id, limit=MEMORY_MAX_TURNS)
        messages = []
        for h in history_raw:
            if h.get("UserMessage"):
                messages.append({"role": "user", "content": h["UserMessage"]})
            if h.get("BotResponse"):
                messages.append({"role": "assistant", "content": h["BotResponse"]})

        async with self._lock:
            self._cache[key] = deque(messages, maxlen=MEMORY_MAX_TURNS * 2)
        return messages

    async def add_exchange(self, bot_id: str, user_id: str, user_msg: str, bot_response: str):
        """เพิ่มคู่สนทนาใหม่เข้า cache"""
        key = self._key(bot_id, user_id)
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = deque(maxlen=MEMORY_MAX_TURNS * 2)
            self._cache[key].append({"role": "user", "content": user_msg})
            self._cache[key].append({"role": "assistant", "content": bot_response})

            # ถ้า cache ใหญ่เกิน threshold → สร้าง summary
            turn_count = len(self._cache[key]) // 2
            if turn_count >= MEMORY_SUMMARY_THRESHOLD and key not in self._summaries:
                # ดึง 10 ข้อความแรกมาสรุป (non-blocking)
                old_msgs = list(self._cache[key])[:20]
                asyncio.ensure_future(self._create_summary(key, old_msgs))

    async def _create_summary(self, key: str, old_messages: List[Dict]):
        """ให้ AI สรุปบทสนทนาเก่าเป็น context สั้นๆ"""
        try:
            summary_text = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in old_messages])
            summary_prompt = (
                "สรุปบทสนทนาต่อไปนี้เป็นภาษาไทย กระชับไม่เกิน 3 บรรทัด "
                "เน้นข้อมูลสำคัญที่ต้องจำ: ชื่อ ปัญหา ความต้องการ สิ่งที่ตกลงกัน:\n\n"
                f"{summary_text}"
            )
            result = await call_claude(
                [{"role": "user", "content": summary_prompt}],
                "คุณเป็น AI ที่สรุปบทสนทนาให้กระชับและมีสาระ",
                key.split(":")[0],
            )
            if result:
                self._summaries[key] = result
                logger.info(f"[MEMORY] Created summary for {key}: {result[:80]}")
        except Exception as e:
            logger.warning(f"[MEMORY] Summary creation failed: {e}")

    def get_summary(self, bot_id: str, user_id: str) -> Optional[str]:
        """ดึงสรุปบทสนทนาเก่า (ถ้ามี)"""
        key = self._key(bot_id, user_id)
        return self._summaries.get(key)

    async def clear(self, bot_id: str, user_id: str):
        """ล้าง cache สำหรับ user"""
        key = self._key(bot_id, user_id)
        async with self._lock:
            self._cache.pop(key, None)
            self._summaries.pop(key, None)

# Global conversation memory instance
conversation_memory = ConversationMemory()

# ==================== Unified People Intelligence ====================
# ระบบจำคนอัจฉริยะ — รู้จักทุกคนข้ามบอท ตั้งแต่วินาทีแรกที่เข้ามา

# ทีมบริหาร (seed data — ข้อมูลเริ่มต้นที่รู้แน่นอน)
_SEED_MANAGEMENT = {
    "U2c6f36e1a490028e4931cce1bc246b70": {"name": "วรวัจน์", "nickname": "CEO วรวัจน์", "role": "CEO/Founder", "is_management": True},
    "U4e6368ef91c7be69efe017c187181625": {"name": "วรวัจน์", "nickname": "CEO วรวัจน์", "role": "CEO/Founder", "is_management": True},
    "U507d4449250cce0cd23b0f51465a7b6a": {"name": "วรวัจน์", "nickname": "CEO วรวัจน์", "role": "CEO/Founder", "is_management": True},
    "Ucebe552553cd5897128d112bd2611e07": {"name": "Game", "nickname": "เกมส์", "role": "IT Manager/COO", "is_management": True},
    "U80cce47038ca3e9fe8ce28bcb8230b94": {"name": "Game", "nickname": "เกมส์", "role": "IT Manager/COO", "is_management": True},
    "U2808964fb15a46fed7156fbdf421b6dd": {"name": "Baipare", "nickname": "ใบแพร", "role": "Marketing", "is_management": True},
    "U7640b070e595c168fed2254fc6d9d3fa": {"name": "Baipare", "nickname": "ใบแพร", "role": "Marketing", "is_management": True},
    "U90b5bc2c98532383d958117761f0a10e": {"name": "Wan", "nickname": "วรรณ", "role": "Coordinator", "is_management": True},
    "Ucacc2f3f13c2b59a67b9d1d115f7a653": {"name": "Wan", "nickname": "วรรณ", "role": "Coordinator", "is_management": True},
    "Ude3f7216df72dfeb74e182905be2cab1": {"name": "Som", "nickname": "ส้ม อัญมณี", "role": "Production", "is_management": True},
    "Ub1ec883267da395546ddd12fabbffe20": {"name": "Som", "nickname": "ส้ม อัญมณี", "role": "Production", "is_management": True},
    "Uf1a7673c4737ad7dd851297a413eabc9": {"name": "Pam", "nickname": "แพม", "role": "Sales", "is_management": True},
    # ทีมสนาม
    "Ua505ea00528a7464a725dd1b1004c705": {"name": "สจ.โอ", "nickname": "สจ.โอ", "role": "Production Coordinator วังชิ้น", "is_management": False},
    "U161bfb57a7467959b15b3d45f7449ada": {"name": "สจ.โอ", "nickname": "สจ.โอ", "role": "Production Coordinator วังชิ้น", "is_management": False},
    "U546d02954d15527dad2ddce6e39b5e59": {"name": "สจ.โอ", "nickname": "สจ.โอ", "role": "Production Coordinator วังชิ้น", "is_management": False},
    "U5bb4a14eadeaed042bd6cab933e9317f": {"name": "ธิติพร", "nickname": "ธิติพร", "role": "CC all reports", "is_management": False},
    "U53497df6556e486f0fd8267abb70fbb0": {"name": "ธิติพร", "nickname": "ธิติพร", "role": "CC all reports", "is_management": False},
    "Uba34968968bcdc74fe99355717f5b82f": {"name": "ธิติพร", "nickname": "ธิติพร", "role": "CC all reports", "is_management": False},
    "Ue3da296d87f90d110fe5fc7a071f43fb": {"name": "อุ๋ย", "nickname": "aui", "role": "Accounting", "is_management": False},
    "U95169bc257fd4436e3c5c59c0fcb4d47": {"name": "อุ๋ย", "nickname": "aui", "role": "Accounting", "is_management": False},
}


class PeopleIntelligence:
    """ระบบจำคนอัจฉริยะ — cache ข้ามบอท + auto-learn จากทุก interaction + จำสมาชิกกลุ่ม"""

    def __init__(self):
        # user_id → {name, nickname, role, is_management, display_name, first_seen, bots_seen: set, groups: set}
        self._people: Dict[str, Dict] = {}
        self._groups: Dict[str, set] = {}  # group_id → set of user_ids (สมาชิกในกลุ่ม)
        self._lock = asyncio.Lock()
        # โหลด seed data
        for uid, info in _SEED_MANAGEMENT.items():
            self._people[uid] = {**info, "display_name": info["name"], "first_seen": "seed", "bots_seen": set(), "groups": set()}

    async def identify(self, user_id: str, bot_id: str, display_name: str = "", group_id: str = "") -> Dict:
        """จำคนทันที — ถ้ารู้จักคืนข้อมูลเลย ถ้าไม่รู้จักเรียนรู้ทันที + จำว่าอยู่กลุ่มไหน"""
        async with self._lock:
            if user_id in self._people:
                person = self._people[user_id]
                person["bots_seen"].add(bot_id)
                if display_name and (not person.get("display_name") or person["display_name"] == "ท่าน"):
                    person["display_name"] = display_name
                    # อัพเดทชื่อด้วยถ้ายังไม่มี
                    if person.get("name", "") in ("ท่าน", ""):
                        person["name"] = display_name
                    if not person.get("nickname"):
                        person["nickname"] = display_name
                if group_id:
                    person.setdefault("groups", set()).add(group_id)
                    self._groups.setdefault(group_id, set()).add(user_id)
                return dict(person)

            # คนใหม่ — เรียนรู้ทันที
            groups_set = {group_id} if group_id else set()
            new_person = {
                "name": display_name or "ท่าน",
                "nickname": display_name or "",
                "role": "unknown",
                "is_management": False,
                "display_name": display_name,
                "first_seen": datetime.now().isoformat(),
                "bots_seen": {bot_id},
                "groups": groups_set,
            }
            self._people[user_id] = new_person
            if group_id:
                self._groups.setdefault(group_id, set()).add(user_id)
            logger.info(f"[PEOPLE] New person learned: {display_name} ({user_id[:10]}...) via {bot_id}")
            return dict(new_person)

    def search_by_name(self, query: str) -> List[Dict]:
        """ค้นหาคนตามชื่อ — ใช้สำหรับประสานงาน เช่น 'หาคุณแพม'"""
        query_lower = query.lower().strip()
        results = []
        for uid, info in self._people.items():
            name = (info.get("name", "") or "").lower()
            nickname = (info.get("nickname", "") or "").lower()
            display = (info.get("display_name", "") or "").lower()
            if query_lower in name or query_lower in nickname or query_lower in display:
                results.append({"user_id": uid, **info})
        return results

    def get_group_members(self, group_id: str) -> List[Dict]:
        """ดึงรายชื่อสมาชิกทั้งหมดในกลุ่ม — บอทรู้ว่าใครอยู่กลุ่มเดียวกัน"""
        member_ids = self._groups.get(group_id, set())
        members = []
        for uid in member_ids:
            info = self._people.get(uid, {})
            members.append({
                "user_id": uid,
                "name": info.get("display_name") or info.get("name", ""),
                "role": info.get("role", "unknown"),
            })
        return members

    def get_group_context_for_ai(self, group_id: str) -> str:
        """สร้าง context สมาชิกกลุ่มสำหรับ AI — บอทรู้ว่าใครอยู่ในกลุ่มนี้"""
        members = self.get_group_members(group_id)
        if not members:
            return ""
        member_list = []
        for m in members[:30]:  # จำกัด 30 คนไม่ให้ context ยาวเกิน
            role_str = f" ({m['role']})" if m['role'] != 'unknown' else ""
            member_list.append(f"{m['name']}{role_str}")
        return (
            f"\n[สมาชิกในกลุ่มนี้ {len(members)} คน] "
            + ", ".join(member_list)
            + "\nคุณจำทุกคนในกลุ่มนี้ได้ เรียกชื่อได้เลย สามารถประสานงานข้ามคนในกลุ่มได้"
        )

    async def learn_from_staff_registry(self, records: List[Dict]):
        """Sync จาก StaffRegistry — อัพเดทข้อมูลทั้งหมด"""
        async with self._lock:
            for record in records:
                # scan all ID columns
                id_fields = {
                    "4": "phrae555", "5": "execcopilot", "6": "aiphrae",
                }
                name = record.get("1", record.get("2", ""))
                nickname = record.get("2", "")
                role = record.get("3", "unknown")
                is_mgmt = role in ["CEO/Founder", "IT Manager/COO", "Marketing", "Coordinator",
                                    "Production / หัวหน้ากลุ่ม Jewelry", "Sales / เซลล์"]

                for col, bot in id_fields.items():
                    uid = record.get(col, "")
                    if uid and uid.startswith("U"):
                        if uid not in self._people:
                            self._people[uid] = {
                                "name": name, "nickname": nickname, "role": role,
                                "is_management": is_mgmt, "display_name": name,
                                "first_seen": "registry", "bots_seen": set(),
                            }
                        else:
                            # อัพเดทข้อมูลจาก registry (เชื่อถือมากกว่า)
                            self._people[uid]["role"] = role
                            if nickname:
                                self._people[uid]["nickname"] = nickname
            logger.info(f"[PEOPLE] Registry synced — total known: {len(self._people)} people")

    async def update_role(self, user_id: str, role: str, is_management: bool = False):
        """อัพเดทตำแหน่งคน (เช่น เลื่อนตำแหน่ง)"""
        async with self._lock:
            if user_id in self._people:
                self._people[user_id]["role"] = role
                self._people[user_id]["is_management"] = is_management

    def is_management(self, user_id: str) -> bool:
        """เช็คว่าเป็นทีมบริหารหรือไม่"""
        person = self._people.get(user_id)
        return person.get("is_management", False) if person else False

    def get_staff_info(self, user_id: str) -> Optional[Dict]:
        """ดึงข้อมูลคน"""
        return self._people.get(user_id)

    def get_context_for_ai(self, user_id: str) -> str:
        """สร้าง context สำหรับ AI — บอทรู้ว่าคุยกับใคร"""
        person = self._people.get(user_id)
        if not person:
            return "\n[สิทธิ์ผู้ใช้] ไม่รู้จักคนนี้ — ต้อนรับและถามชื่อ ห้ามเปิดเผยข้อมูลลับ"

        name = person.get("nickname") or person.get("name", "")
        role = person.get("role", "unknown")

        if person.get("is_management"):
            return (
                f"\n[ข้อมูลทีมงาน] กำลังคุยกับ: {name} ({role}) — "
                f"เป็นทีมบริหาร สามารถเปิดเผยข้อมูลลับได้ เรียกชื่อเล่นได้เลย"
            )
        elif role != "unknown":
            return (
                f"\n[ข้อมูลทีมงาน] กำลังคุยกับ: {name} ({role}) — "
                f"เป็นทีมงาน แต่ไม่ใช่ทีมบริหาร ห้ามเปิดเผยข้อมูลลับบริษัท"
            )
        else:
            return (
                f"\n[สิทธิ์ผู้ใช้] คนนี้ชื่อ {name} — ยังไม่รู้ตำแหน่ง "
                f"คุยได้ทุกเรื่อง ช่วยเต็มที่ แต่ห้ามเปิดเผยข้อมูลลับ"
            )

    @property
    def total_known(self) -> int:
        return len(self._people)


# Global People Intelligence instance
people = PeopleIntelligence()


# Legacy compatibility functions
def is_management(user_id: str) -> bool:
    return people.is_management(user_id)

def get_staff_info(user_id: str) -> Optional[Dict]:
    return people.get_staff_info(user_id)


# ==================== Rate Limiting ====================
_ai_semaphore = asyncio.Semaphore(5)

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
    """แจ้ง CEO ผ่าน LINE ExecCopilot + Log ลง monitor"""
    try:
        await monitor.log_message(
            bot_id=bot_id, bot_name=BOTS_CONFIG.get(bot_id, {}).get("name", bot_id),
            sender="SYSTEM", message_in=f"[ERROR] {error_type}",
            message_out=detail[:200], msg_type="error",
            ai_used="none", status="error", response_ms=0,
        )
        logger.error(f"[ALERT] {bot_id} — {error_type}: {detail}")

        # ส่งแจ้ง CEO ผ่าน LINE ExecCopilot (ถ้ามี token)
        ceo_line_id = "U4e6368ef91c7be69efe017c187181625"  # CEO ExecCopilot ID
        env = get_env_vars()
        exec_token = env.get("execcopilot", {}).get("token", "")
        if exec_token:
            alert_msg = f"⚠️ [{error_type}]\nBot: {bot_id}\n{detail[:300]}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    "https://api.line.me/v2/bot/message/push",
                    headers={"Authorization": f"Bearer {exec_token}", "Content-Type": "application/json"},
                    json={"to": ceo_line_id, "messages": [{"type": "text", "text": alert_msg}]},
                )
    except Exception as e:
        logger.error(f"Alert failed: {e}")


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


async def line_get_user_profile(bot_id: str, user_id: str, group_id: str = "") -> Optional[Dict]:
    """ดึงโปรไฟล์ผู้ใช้จาก LINE — ลอง friend API ก่อน ถ้าไม่ได้ลอง group API"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. ลอง Friend Profile API (ใช้ได้เมื่อ add เป็นเพื่อน)
            resp = await client.get(
                f"https://api.line.me/v2/bot/profile/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()

            # 2. Fallback: Group Member Profile API (ใช้ได้เมื่ออยู่ในกลุ่มเดียวกัน)
            if group_id:
                resp2 = await client.get(
                    f"https://api.line.me/v2/bot/group/{group_id}/member/{user_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp2.status_code == 200:
                    return resp2.json()
    except:
        pass
    return None


async def line_get_group_member_profile(bot_id: str, group_id: str, user_id: str) -> Optional[Dict]:
    """ดึงโปรไฟล์สมาชิกในกลุ่ม — ใช้ได้แม้ไม่ได้ add เพื่อน"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"https://api.line.me/v2/bot/group/{group_id}/member/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return None


async def line_get_group_member_ids(bot_id: str, group_id: str) -> List[str]:
    """ดึง user ID ของสมาชิกทุกคนในกลุ่ม — pagination อัตโนมัติ"""
    env = get_env_vars()
    token = env.get(bot_id, {}).get("token", "")
    if not token:
        return []
    all_ids = []
    continuation_token = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for _ in range(20):  # max 20 pages (ป้องกัน infinite loop)
                url = f"https://api.line.me/v2/bot/group/{group_id}/members/ids"
                params = {}
                if continuation_token:
                    params["start"] = continuation_token
                resp = await client.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
                if resp.status_code != 200:
                    logger.warning(f"[GROUP-SCAN] Failed to get member IDs: HTTP {resp.status_code}")
                    break
                data = resp.json()
                member_ids = data.get("memberIds", [])
                all_ids.extend(member_ids)
                continuation_token = data.get("next")
                if not continuation_token:
                    break
    except Exception as e:
        logger.error(f"[GROUP-SCAN] Error getting member IDs: {e}")
    return all_ids


# ==================== Group Scan Intelligence ====================
# สแกนสมาชิกในกลุ่มทั้งหมด — จำทุกคนทันทีที่บอทเข้ากลุ่ม/ได้รับข้อความ

_scanned_groups: Dict[str, float] = {}  # group_key → last_scan_timestamp
GROUP_SCAN_INTERVAL = 3600  # rescan ทุก 1 ชั่วโมง


async def scan_group_members(bot_id: str, group_id: str, force: bool = False) -> int:
    """สแกนสมาชิกทุกคนในกลุ่ม → จำทุกคนผ่าน PeopleIntelligence
    Returns: จำนวนคนที่เรียนรู้ใหม่"""
    scan_key = f"{bot_id}:{group_id}"
    now = time.time()

    # เช็คว่าเพิ่งสแกนไปหรือยัง (ป้องกันสแกนซ้ำถี่เกินไป)
    if not force and scan_key in _scanned_groups:
        elapsed = now - _scanned_groups[scan_key]
        if elapsed < GROUP_SCAN_INTERVAL:
            return 0

    _scanned_groups[scan_key] = now
    logger.info(f"[GROUP-SCAN] Starting scan: bot={bot_id}, group={group_id[:15]}...")

    # ดึง member IDs ทั้งหมด
    member_ids = await line_get_group_member_ids(bot_id, group_id)
    if not member_ids:
        logger.warning(f"[GROUP-SCAN] No members found or API failed for group {group_id[:15]}")
        return 0

    new_learned = 0
    for uid in member_ids:
        # ดึงโปรไฟล์สมาชิกผ่าน Group API (ไม่ต้อง add เพื่อน!)
        profile = await line_get_group_member_profile(bot_id, group_id, uid)
        display_name = profile.get("displayName", "") if profile else ""

        # จำคนทันที
        person_data = await people.identify(uid, bot_id, display_name, group_id=group_id)
        if person_data.get("first_seen") != "seed" and person_data.get("first_seen") != "registry":
            new_learned += 1

        # ลงทะเบียนอัตโนมัติ (non-blocking)
        if display_name:
            asyncio.ensure_future(auto_register_user(bot_id, uid, display_name, "group_scan"))

        # Rate limit — ไม่ยิง API ถี่เกินไป
        await asyncio.sleep(0.1)

    logger.info(f"[GROUP-SCAN] Done: bot={bot_id}, group={group_id[:15]}, "
                f"total_members={len(member_ids)}, new_learned={new_learned}, "
                f"total_known={people.total_known}")
    return new_learned


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

    # 1. ดึงประวัติบทสนทนาจาก Memory Cache (เร็ว!) + โปรไฟล์ผู้ใช้
    history_msgs, profile = await asyncio.gather(
        conversation_memory.get_history(bot_id, user_id),
        airtable_get_user_profile(user_id),
    )

    # 2. สร้าง context เพิ่มเติม
    extra_context = ""
    if profile:
        extra_context += f"\n[ข้อมูลผู้ใช้] ชื่อ: {profile.get('name', display_name)}"
        for key in ['location', 'crops', 'farmSize', 'phone', 'notes']:
            if profile.get(key):
                extra_context += f" | {key}: {profile[key]}"

    # เพิ่ม conversation summary ถ้ามี (สรุปบทสนทนาเก่า)
    memory_summary = conversation_memory.get_summary(bot_id, user_id)
    if memory_summary:
        extra_context += f"\n[สรุปบทสนทนาก่อนหน้า] {memory_summary}"

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

    # 5. People Intelligence — บอทรู้ว่าคุยกับใคร ทันทีที่เจอ
    person_info = await people.identify(user_id, bot_id, display_name)
    staff_context = people.get_context_for_ai(user_id)

    # 6. สร้าง system prompt เต็ม
    full_system = system_prompt
    if extra_context:
        full_system += f"\n\n{extra_context}"
    if staff_context:
        full_system += f"\n\n{staff_context}"
    if image_analysis:
        full_system += f"\n\n{image_analysis}"
    if search_result:
        full_system += f"\n\n{search_result}"

    # 7. สร้าง messages array จาก Memory Cache (ใช้ล่าสุด 16 ข้อความ = 8 คู่สนทนา)
    messages = history_msgs[-16:] if len(history_msgs) > 16 else list(history_msgs)

    # เพิ่มข้อความปัจจุบัน
    current_msg = message_text
    if message_type == "image":
        current_msg = f"[ผู้ใช้ส่งรูปภาพมา]{' ' + message_text if message_text else ''}"
        if image_analysis:
            current_msg += f"\n{image_analysis}"

    messages.append({"role": "user", "content": f"[{display_name}]: {current_msg}"})

    # 8. เรียก Claude — สมองหลัก (with rate limiting)
    async with _ai_semaphore:
        response = await call_claude(messages, full_system, bot_id)

    # 9. Fallback cascade ถ้า Claude ล้มเหลว
    if not response:
        logger.warning(f"Claude failed for {bot_id}, trying Gemini...")
        async with _ai_semaphore:
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

        # จัดการ memberJoined event — คนใหม่เข้ากลุ่ม → จำทันที
        if event_type == "memberJoined":
            joined_members = event.get("joined", {}).get("members", [])
            group_id_join = event.get("source", {}).get("groupId", "")
            reply_token_join = event.get("replyToken", "")
            bot_display_join = BOTS_CONFIG.get(bot_id, {}).get("name", "บอท")

            for member in joined_members:
                member_uid = member.get("userId", "")
                if not member_uid:
                    continue
                # ดึงโปรไฟล์ + จำคนทันที
                member_profile = await line_get_user_profile(bot_id, member_uid)
                member_name = member_profile.get("displayName", "คุณ") if member_profile else "คุณ"
                person_data = await people.identify(member_uid, bot_id, member_name, group_id=group_id_join)
                asyncio.ensure_future(auto_register_user(bot_id, member_uid, member_name, "group_join"))

                # สร้างข้อความต้อนรับอัจฉริยะ
                if person_data.get("role", "unknown") != "unknown":
                    welcome = (
                        f"สวัสดีค่ะคุณ{person_data.get('nickname', member_name)} 🙏\n"
                        f"น้อง{bot_display_join}จำได้ค่ะ — {person_data.get('role', '')}\n"
                        f"ยินดีช่วยเหลือทุกเรื่องเลยค่ะ พิมพ์ถามมาได้เลยนะคะ 😊"
                    )
                else:
                    welcome = (
                        f"สวัสดีค่ะคุณ{member_name} 🙏\n"
                        f"ยินดีต้อนรับเข้ากลุ่มค่ะ! น้อง{bot_display_join}พร้อมช่วยเหลือทุกเรื่องเลยค่ะ\n"
                        f"พิมพ์ถามมาได้เลยนะคะ 😊"
                    )
                logger.info(f"[MEMBER-JOINED] {member_name} ({member_uid[:10]}...) joined group via {bot_id}, known_role={person_data.get('role')}")

            # ตอบต้อนรับ (ใช้ข้อความสุดท้าย)
            if joined_members and reply_token_join:
                await line_reply(bot_id, reply_token_join, welcome, user_id=joined_members[-1].get("userId", ""))

            # Group Scan — สแกนสมาชิกทั้งกลุ่มเมื่อมีคนใหม่เข้า (background)
            if group_id_join:
                asyncio.ensure_future(scan_group_members(bot_id, group_id_join))
            continue

        # จัดการ follow event — ลงทะเบียนอัตโนมัติ + ต้อนรับ
        if event_type == "follow":
            follow_user_id = event.get("source", {}).get("userId", "unknown")
            logger.info(f"[{bot_id}] New follower: {follow_user_id}")
            # ดึงโปรไฟล์แล้วลงทะเบียน + จำคนทันที
            follow_profile = await line_get_user_profile(bot_id, follow_user_id)
            follow_name = follow_profile.get("displayName", "คุณ") if follow_profile else "คุณ"
            await people.identify(follow_user_id, bot_id, follow_name)
            asyncio.ensure_future(auto_register_user(bot_id, follow_user_id, follow_name, "follow"))
            bot_display = BOTS_CONFIG.get(bot_id, {}).get("name", "บอท")
            person_data = people.get_staff_info(follow_user_id)
            if person_data and person_data.get("role", "unknown") != "unknown":
                welcome_msg = (
                    f"สวัสดีค่ะคุณ{person_data.get('nickname', follow_name)} 🙏\n"
                    f"น้อง{bot_display}จำได้ค่ะ! คุณ{person_data.get('nickname', follow_name)} — {person_data.get('role', '')}\n"
                    f"พร้อมช่วยเหลือทุกเรื่องเลยค่ะ พิมพ์ถามมาได้เลยนะคะ 😊"
                )
            else:
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

        # ดึง display name + จำคนทันที (ใช้ group API ถ้าอยู่ในกลุ่ม)
        profile = await line_get_user_profile(bot_id, user_id, group_id=group_id)
        display_name = profile.get("displayName", "ท่าน") if profile else "ท่าน"
        await people.identify(user_id, bot_id, display_name, group_id=group_id)

        # ลงทะเบียนอัตโนมัติ (non-blocking)
        asyncio.ensure_future(auto_register_user(bot_id, user_id, display_name, source_type))

        # Group Scan Intelligence — สแกนสมาชิกทั้งกลุ่มเมื่อได้รับข้อความจากกลุ่ม
        # ทำ background เพื่อไม่ให้ช้า + ป้องกันสแกนซ้ำด้วย interval
        if is_group and group_id:
            asyncio.ensure_future(scan_group_members(bot_id, group_id))

        # เรียกสมอง AI — ถ้าอยู่ในกลุ่ม เพิ่ม context ให้ AI ตัดสินใจเองว่าจะตอบ
        group_context = ""
        if is_group:
            # สร้าง context รายชื่อสมาชิกในกลุ่ม — บอทรู้จักทุกคน
            members_context = people.get_group_context_for_ai(group_id) if group_id else ""
            group_context = (
                "\n\n[บริบทกลุ่มแชท] คุณอยู่ในกลุ่มแชท LINE ของทีมงาน "
                "ให้วิเคราะห์ข้อความที่เข้ามาด้วยสมอง AI ของคุณ:\n"
                "- ถ้าข้อความเกี่ยวข้องกับงานของคุณ หรือเป็นคำถาม หรือต้องการความช่วยเหลือ → ตอบตามปกติ\n"
                "- ถ้ามีคนเรียกชื่อคุณ หรือพูดถึงบทบาทของคุณ → ตอบทันที\n"
                "- ถ้าเป็นคนใหม่ทักมาครั้งแรก → ต้อนรับและแนะนำตัว\n"
                "- ถ้ามีคนถามถึงคนอื่นในกลุ่ม → ช่วยประสานงาน เรียกชื่อเค้าได้เลย\n"
                "- ถ้าเป็นแค่คำทักทายทั่วไประหว่างคนในกลุ่ม สติกเกอร์ หรือ emoji → ตอบ [SKIP] เพียงอย่างเดียว (ห้ามพูดอื่น)\n"
                "- ถ้าข้อความไม่เกี่ยวข้องกับงานของคุณเลย → ตอบ [SKIP] เพียงอย่างเดียว\n"
                "สำคัญ: ถ้าตัดสินใจไม่ตอบ ให้ตอบ [SKIP] เท่านั้น ห้ามมีข้อความอื่น"
                + members_context
            )

        try:
            # ส่ง "กำลังคิด..." ทันที (ใช้ reply token ก่อนหมดอายุ 30 วินาที)
            # แล้วส่งคำตอบจริงตามมาด้วย Push API
            if not is_group and reply_token:
                try:
                    env_vars = get_env_vars()
                    tk = env_vars.get(bot_id, {}).get("token", "")
                    if tk:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            await client.post(
                                "https://api.line.me/v2/bot/message/reply",
                                headers={"Authorization": f"Bearer {tk}", "Content-Type": "application/json"},
                                json={"replyToken": reply_token, "messages": [
                                    {"type": "text", "text": f"กำลังคิด... 🧠"}
                                ]},
                            )
                        reply_token = ""  # ใช้ reply token ไปแล้ว ต่อไปใช้ Push
                except Exception:
                    pass  # ไม่เป็นไร ถ้าส่งไม่ได้จะใช้ reply token ตอบจริงแทน

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
            # ส่งแจ้งเตือน CEO ทันทีผ่าน LINE
            asyncio.ensure_future(send_error_alert(bot_id, "AI_BRAIN_ERROR", str(e)))

        # ถ้า AI ตัดสินใจ [SKIP] → ไม่ตอบในกลุ่ม
        if is_group and ai_response and "[SKIP]" in ai_response:
            logger.info(f"[GROUP-SKIP] {bot_name} chose not to respond to: {msg_text[:50]}")
            continue

        # ตอบกลับ LINE (Reply API ก่อน → Push API fallback)
        await line_reply(bot_id, reply_token, ai_response, user_id=user_id)

        # บันทึกลง Memory Cache (เร็ว) + Airtable (non-blocking, backup)
        user_msg_text = msg_text if msg_type == "text" else f"[{msg_type}]"
        asyncio.ensure_future(conversation_memory.add_exchange(
            bot_id, user_id,
            f"[{display_name}]: {user_msg_text}",
            ai_response,
        ))
        asyncio.ensure_future(airtable_save_message(
            user_id, bot_id, display_name,
            user_msg_text,
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


@app.on_event("startup")
async def startup_sync_people():
    """เมื่อ server เริ่มทำงาน — sync ข้อมูลคนจาก StaffRegistry Google Sheet"""
    try:
        # ดึง StaffRegistry จาก Google Sheets (public CSV)
        sheet_id = "1-lqcruGtJiMzKFS2MK5gqcxaerzt9PiOTxmdTLqe_eM"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(sheet_url)
            if resp.status_code == 200:
                reader = csv.reader(io.StringIO(resp.text))
                rows = list(reader)
                if len(rows) > 1:
                    records = []
                    for row in rows[1:]:
                        record = {str(i): v for i, v in enumerate(row)}
                        records.append(record)
                    await people.learn_from_staff_registry(records)
                    logger.info(f"[STARTUP] People Intelligence synced: {people.total_known} people known")
            else:
                logger.warning(f"[STARTUP] StaffRegistry sync failed: HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"[STARTUP] StaffRegistry sync error: {e} — using seed data only")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.12.1-group-memory-intelligence",
        "brain": "Claude API",
        "vision": "GPT-4o",
        "search": "Perplexity",
        "fallback": "Gemini Flash",
        "database": "Airtable",
        "people_known": people.total_known,
        "groups_scanned": len(_scanned_groups),
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


# ==================== API Endpoints — Railway-native (แทน Make.com) ====================

@app.post("/api/deploy")
async def api_deploy(request: Request):
    """Self-deploy: รับ base64 content + commit message แล้ว push ไป GitHub โดยตรง
    ใช้แทน Make.com deploy pipeline — Railway ทำเองได้"""
    try:
        body = await request.json()
        secret = body.get("secret", "")
        if secret != DEPLOY_SECRET:
            raise HTTPException(status_code=403, detail="Invalid deploy secret")
        if not GITHUB_PAT:
            raise HTTPException(status_code=500, detail="GITHUB_PAT not configured on Railway")

        file_path = body.get("path", "main.py")
        content_b64 = body.get("content")  # base64 encoded file
        message = body.get("message", "deploy via Railway API")

        if not content_b64:
            raise HTTPException(status_code=400, detail="Missing 'content' (base64)")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: GET current SHA
            get_resp = await client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}?ref=main",
                headers={"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json", "User-Agent": "RailwayGateway"},
            )
            if get_resp.status_code != 200:
                return JSONResponse({"error": "Failed to get current SHA", "status": get_resp.status_code}, status_code=500)
            current_sha = get_resp.json().get("sha")

            # Step 2: PUT new content
            put_resp = await client.put(
                f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}",
                headers={"Authorization": f"token {GITHUB_PAT}", "Accept": "application/vnd.github.v3+json", "User-Agent": "RailwayGateway"},
                json={"message": message, "content": content_b64, "sha": current_sha, "branch": "main"},
            )
            if put_resp.status_code in (200, 201):
                commit_sha = put_resp.json().get("commit", {}).get("sha", "unknown")
                logger.info(f"[DEPLOY] Success: {message} — commit {commit_sha[:7]}")
                return {"status": "deployed", "commit": commit_sha, "message": message}
            else:
                return JSONResponse({"error": "GitHub PUT failed", "detail": put_resp.text[:500]}, status_code=500)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DEPLOY] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/people")
async def api_people():
    """ดูคนที่ระบบรู้จักทั้งหมด — สำหรับ debug / monitoring"""
    people_list = []
    for uid, info in people._people.items():
        people_list.append({
            "user_id": uid[:15] + "...",
            "name": info.get("name", ""),
            "nickname": info.get("nickname", ""),
            "role": info.get("role", "unknown"),
            "is_management": info.get("is_management", False),
            "source": info.get("first_seen", ""),
            "bots": list(info.get("bots_seen", set())),
            "groups": len(info.get("groups", set())),
        })
    return {
        "total": len(people_list),
        "groups_scanned": len(_scanned_groups),
        "groups_tracked": len(people._groups),
        "people": sorted(people_list, key=lambda x: (not x["is_management"], x["name"])),
    }


@app.get("/api/people/search")
async def api_people_search(q: str = ""):
    """ค้นหาคนตามชื่อ — เช่น /api/people/search?q=แพม"""
    if not q:
        return {"error": "Missing query parameter ?q="}
    results = people.search_by_name(q)
    return {
        "query": q,
        "found": len(results),
        "results": [
            {
                "name": r.get("name", ""),
                "nickname": r.get("nickname", ""),
                "role": r.get("role", "unknown"),
                "is_management": r.get("is_management", False),
                "groups": len(r.get("groups", set())),
            }
            for r in results
        ],
    }


@app.post("/api/scan-group")
async def api_scan_group(request: Request):
    """สั่งสแกนสมาชิกในกลุ่มด้วยมือ — ใช้เมื่อต้องการ force rescan"""
    try:
        body = await request.json()
        secret = body.get("secret", "")
        if secret != DEPLOY_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")

        bot_id = body.get("bot_id")
        group_id = body.get("group_id")
        if not bot_id or not group_id:
            raise HTTPException(status_code=400, detail="Missing bot_id or group_id")

        new_count = await scan_group_members(bot_id, group_id, force=True)
        return {
            "status": "scanned",
            "bot": bot_id,
            "group": group_id[:15] + "...",
            "new_learned": new_count,
            "total_known": people.total_known,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SCAN-GROUP] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/memory/save")
async def api_memory_save(request: Request):
    """บันทึก Chat Memory ไป Google Sheets โดยตรง (แทน Make.com webhook)"""
    try:
        body = await request.json()
        # Forward to Google Sheets via Sheets API v4
        # ถ้ายังไม่มี service account key ให้ forward ไป Make.com webhook เป็น fallback
        webhook_url = "https://hook.us2.make.com/cz1znn3ansnjyp336ex12vkecunhsxp9"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(webhook_url, json=body)
            return {"status": "saved", "method": "webhook_fallback", "code": resp.status_code}
    except Exception as e:
        logger.error(f"[MEMORY-SAVE] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/memory/load")
async def api_memory_load(request: Request):
    """โหลด Chat Memory จาก Google Sheets โดยตรง"""
    try:
        # ถ้ามี Google Service Key ใช้ Sheets API ตรง ถ้าไม่มีใช้ public CSV export
        sheet_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_ID}/export?format=csv&gid=0"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(sheet_url)
            if resp.status_code == 200:
                reader = csv.reader(io.StringIO(resp.text))
                rows = list(reader)
                return {"status": "loaded", "method": "csv_export", "headers": rows[0] if rows else [], "records": rows[1:] if len(rows) > 1 else []}
            else:
                return JSONResponse({"error": "Failed to load sheet", "status": resp.status_code}, status_code=500)
    except Exception as e:
        logger.error(f"[MEMORY-LOAD] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/line/push")
async def api_line_push(request: Request):
    """Push message ไปหาผู้ใช้ผ่าน LINE — ใช้แทน Make.com LINE Push tools"""
    try:
        body = await request.json()
        secret = body.get("secret", "")
        if secret != DEPLOY_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")

        bot_id = body.get("bot_id", "execcopilot")
        user_id = body.get("user_id")
        message = body.get("message")
        if not user_id or not message:
            raise HTTPException(status_code=400, detail="Missing user_id or message")

        env_vars = get_env_vars()
        token = env_vars.get(bot_id, {}).get("token", "")
        if not token:
            raise HTTPException(status_code=400, detail=f"No token for bot: {bot_id}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"to": user_id, "messages": [{"type": "text", "text": message}]},
            )
            return {"status": "sent" if resp.status_code == 200 else "error", "code": resp.status_code, "bot": bot_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LINE-PUSH] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/line/broadcast")
async def api_line_broadcast(request: Request):
    """Broadcast message ไปหาทุกผู้ติดตาม — ใช้แทน Make.com Broadcast tools"""
    try:
        body = await request.json()
        secret = body.get("secret", "")
        if secret != DEPLOY_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")

        bot_id = body.get("bot_id", "execcopilot")
        message = body.get("message")
        if not message:
            raise HTTPException(status_code=400, detail="Missing message")

        env_vars = get_env_vars()
        token = env_vars.get(bot_id, {}).get("token", "")
        if not token:
            raise HTTPException(status_code=400, detail=f"No token for bot: {bot_id}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.line.me/v2/bot/message/broadcast",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"messages": [{"type": "text", "text": message}]},
            )
            return {"status": "broadcast" if resp.status_code == 200 else "error", "code": resp.status_code, "bot": bot_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LINE-BROADCAST] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ==================== Main ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

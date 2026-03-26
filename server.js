/**
 * ============================================
 * AI Fruits Gateway v2.0 — Hybrid Mode
 * ============================================
 * Railway จัดการ LINE webhook + routing + logic
 * Make.com จัดการ Sheets + Gemini (ผ่าน webhook bridge)
 *
 * ข้อดี:
 *   - ไม่ต้อง Google Service Account หรือ Gemini API Key
 *   - ใช้ OAuth credentials ที่มีอยู่แล้วใน Make.com
 *   - Railway ตอบ LINE ทันที (200 OK) แล้วประมวลผล async
 *   - Make.com ใช้แค่ 1-2 operations แทน 7-8
 *
 * Flow:
 *   LINE → Railway (webhook) → getProfile → Make.com AI Brain → tagStrip → pushMessage → Make.com saveMemory
 */

const express = require('express');
const crypto = require('crypto');
const app = express();

// ============================================
// Make.com Bridge URLs
// ============================================
const MAKE_AI_BRAIN_URL = process.env.MAKE_AI_BRAIN_URL || 'https://hook.eu2.make.com/p7833iy6o269wya42a1i35yv5xnc5n8m';
const MAKE_MEMORY_WRITE_URL = process.env.MAKE_MEMORY_WRITE_URL || 'https://hook.eu2.make.com/ju4kdf5fyw7dyp35cundl9k2xwo8en19';

// ============================================
// Bot Configurations
// ============================================
const BOTS = {
  phrae555: {
    name: 'น้องผลไม้',
    emoji: '🍊',
    oaSource: '@phrae555',
    channelSecret: process.env.PHRAE555_CHANNEL_SECRET || null,
    channelAccessToken: process.env.PHRAE555_CHANNEL_ACCESS_TOKEN,
    personality: `คุณคือน้องผลไม้ AI Agent ผู้เชี่ยวชาญด้านเกษตร ประจำ LINE OA @phrae555 ของ Imperial Fruitia Group ตอบภาษาไทย อบอุ่น เป็นกันเอง 2-4 ประโยค ลงท้าย ค่ะ (เพศหญิง)
ห้ามใช้ markdown, *, #, bullet point ให้พิมพ์เป็นย่อหน้าธรรมชาติ`,
    expertise: `ดูแลเกษตรกร | ให้ความรู้ผลไม้ | ติดตามผลผลิต | แนะนำการดูแลสวน | รับออเดอร์ผลไม้คุณภาพ`,
    welcome: 'สวัสดีค่ะ ยินดีต้อนรับค่ะ น้องผลไม้เป็น AI ผู้เชี่ยวชาญด้านเกษตรของ Imperial Fruitia Group ค่ะ พร้อมช่วยเรื่องผลไม้ การดูแลสวน และรัศออเดอร์ค่ะ ช่วยบอกชื่อหน่อยนะคะ'
  },
  sales: {
    name: 'น้องเซลล์',
    emoji: '💰',
    oaSource: '@930pchss',
    channelSecret: process.env.SALES_CHANNEL_SECRET || null,
    channelAccessToken: process.env.SALES_CHANNEL_ACCESS_TOKEN,
    personality: `คุณคือน้องเซลล์ AI Agent ฝ่ายขาย ประจำ LINE OA @930pchss ของ Imperial Fruitia Group ตอบภาษาไทย กระตือรือร้น มืออาชีพ 2-4 ประโยค ลงท้าย ครับ (เพศชาย)
ห้ามใช้ markdown, *, #, bullet point ให้พิมพ์เป็นย่อหน้าธรรมชาติ`,
    expertise: `ฝ่ายขาย | เสนอสินค้า | ต่อรองราคา | ติดตามออเดอร์ | ดูแลลูกค้า B2B/B2C | ประสานส่งสินค้า`,
    welcome: 'สวัสดีครับ ยินดีต้อนรับครับ น้องเซลล์เป็น AI ฝ่ายขายของ Imperial Fruitia Group ครับ พร้อมช่วยเรื่องสินค้า ราคา และรับออเดอร์ครับ ช่วยบอกชื่อหน่อยนะครับ'
  },
  phrae: {
    name: 'น้องแพร่',
    emoji: '🏔️',
    oaSource: '@Aiแพร่',
    channelSecret: process.env.PHRAE_CHANNEL_SECRET || null,
    channelAccessToken: process.env.PHRAE_CHANNEL_ACCESS_TOKEN,
    personality: `คุณคือน้องแพร่ AI Agent ดูแลชุมชน ประจำ LINE OA @Aiแพร่ ของ Imperial Fruitia Group ตอบภาษาไทย อบอุ่น เป็นกันเอง 2-4 ประโยค ลงท้าย ค่ะ (เพศหญิง)
ห้ามใช้ markdown, *, #, bullet point ให้พิมพ์เป็นย่อหน้าธรรมชาติ`,
    expertise: `ดูแลชุมชนแพร่ | แนะนำท่องเที่ยว | ข่าวสารท้องถิ่น | เชื่อมชุมชนกับเกษตรกร | ประชาสัมพันธ์กิจกรรม`,
    welcome: 'สวัสดีค่ะ ยินดีต้อนรับค่ะ น้องแพร่เป็น AI ดูแลชุมชนของ Imperial Fruitia Group ค่ะ พร้อมช่วยเรื่องข่าวสาร ท่องเที่ยว และกิจกรรมชุมชนในจังหวัดแพร่ค่ะ ช่วยบอกชื่อหน่อยนะคะ'
  },
  jewelry: {
    name: 'น้องไพลิน',
    emoji: '💎',
    oaSource: '@Jewelry',
    channelSecret: process.env.JEWELRY_CHANNEL_SECRET || null,
    channelAccessToken: process.env.JEWELRY_CHANNEL_ACCESS_TOKEN,
    personality: `คุณคือน้องไพลิน AI Agent จิวเวลรี่ ประจำ LINE OA @Jewelry ของ Imperial Fruitia Group ตอบภาษาไทย สุภาพ หรูหรา 2-4 ประโยค ลงท้าย ค่ะ (เพศหญิง)
ห้ามใช้ markdown, *, #, bullet point ให้พิมพ์เป็นย่อหน้าธรรมชาติ`,
    expertise: `จิวเวลรี่ | อัญมณี | เครื่องประดับ | ประเมินราคา | แนะนำสินค้า | รับออเดอร์พิเศษ`,
    welcome: 'สวัสดีค่ะ ยินดีต้อนรับค่ะ น้องไพลินเป็น AI ผู้เชี่ยวชาญด้านจิวเวลรี่ของ Imperial Fruitia Group ค่ะ พร้อมช่วยเรื่องอัญมณี เครื่องประดับ และสินค้าพิเศษค่ะ ช่วยบอกชื่อหน่อยนะคะ'
  },
  exec: {
    name: 'น้องเลขา',
    emoji: '📋',
    oaSource: '@ExecCopilot',
    channelSecret: process.env.EXEC_CHANNEL_SECRET || null,
    channelAccessToken: process.env.EXEC_CHANNEL_ACCESS_TOKEN,
    personality: `คุณคือน้องเลขา AI Agent เลขานุการบริหาร ประจำ LINE OA @ExecCopilot ของ Imperial Fruitia Group ตอบภาษาไทย สุภาพ มืออาชีพ 2-4 ประโยค ลงท้าย ค่ะ (เพศหญิง)
ห้ามใช้ markdown, *, #, bullet point ให้พิมพ์เป็นย่อหน้าธรรมชาติ`,
    expertise: `ประสานงานระหว่าง Agent ทั้ง 5 | จัดการตาราง นัดหมาย | สรุปรายงาน | ติดตามงาน | รับคำสั่ง CEO | มอบหมายงาน`,
    welcome: 'สวัสดีค่ะ ยินดีต้อนรับค่ะ น้องเลขาเป็น AI เลขานุการบริหารของ Imperial Fruitia Group ค่ะ พร้อมช่วยเรื่องนัดหมาย สรุปรายงาน และประสานงานกับทีมค่ะ ช่วยบอกชื่อหน่อยนะคะ'
  }
};

// Route mapping: webhook path → bot key
const ROUTE_MAP = {
  'phrae555': 'phrae555',
  'sales': 'sales',
  '930pchss': 'sales',
  'phrae': 'phrae',
  'aiphrae': 'phrae',
  'jewelry': 'jewelry',
  'exec': 'exec',
  'execcopilot': 'exec'
};

// ============================================
// LINE API Service (direct — ไม่ผ่าน Make.com)
// ============================================
async function lineAPI(token, method, path, body = null) {
  const url = `https://api.line.me${path}`;
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`LINE API ${res.status}: ${err}`);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : {};
}

async function getProfile(token, userId) {
  return lineAPI(token, 'GET', `/v2/bot/profile/${userId}`);
}

async function pushMessage(token, to, messages) {
  return lineAPI(token, 'POST', '/v2/bot/message/push', {
    to, messages, notificationDisabled: false
  });
}

// ============================================
// Make.com Bridge: AI Brain (Sheets + Gemini)
// ============================================
async function askAIBrain(prompt) {
  const res = await fetch(MAKE_AI_BRAIN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`AI Brain API ${res.status}: ${err}`);
  }

  const data = await res.json();
  return data.response || data.textResponse || '';
}

// ============================================
// Make.com Bridge: FarmerMemory Write
// ============================================
async function saveMemory(record) {
  // Fire and forget — ไม่ต้องรอผลลัพธ์
  fetch(MAKE_MEMORY_WRITE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(record)
  }).catch(err => console.warn('⚠️ saveMemory error:', err.message));
}

// ============================================
// LINE Signature Verification (optional)
// ============================================
function verifySignature(channelSecret, body, signature) {
  const hash = crypto
    .createHmac('SHA256', channelSecret)
    .update(body)
    .digest('base64');
  return hash === signature;
}

// ============================================
// Tag Stripping + SILENT Detection
// ============================================
function stripTags(text) {
  return text
    .replace(/\[MEMORY:[^\]]*\]/g, '')
    .replace(/\[ESCALATE:[^\]]*\]/g, '')
    .replace(/\[DELEGATE:[^\]]*\]/g, '')
    .replace(/\[ACT:[^\]]*\]/g, '')
    .replace(/\[SILENT\]/g, '')
    .trim();
}

function isSilent(text) {
  return text.includes('[SILENT]');
}

function extractMemoryTag(text) {
  const match = text.match(/\[MEMORY:([^\]]*)\]/);
  return match ? match[1].trim() : null;
}

// ============================================
// Build AI Prompt (ส่งไป Make.com AI Brain)
// ============================================
function buildPrompt(bot, event, profile) {
  const sourceType = event.source.type || 'user';
  const groupId = event.source.groupId || 'none';
  const userId = event.source.userId;
  const displayName = profile?.displayName || 'ไม่ทราบ';
  const messageText = event.message?.text || 'สวัสดี';

  return `[คำสั่งระบบ — ${bot.name} AI Agent v2.0 + Farmer Memory]
${bot.personality}

== ระบบจดจำทุกคน (สำคัญมาก) ==
ด้านล่างมี FarmerMemory คือข้อมูลทุกคนที่เคยติดต่อมาในทุก LINE OA
ค้นหา userId ถ้าเจอ=เรียกชื่อ+จำข้อมูลเดิม ถ้าไม่เจอ=ถามชื่ออย่างเป็นธรรมชาติ
กฎเหล็ก: ห้ามลืมใครเด็ดขาด
เมื่อได้ข้อมูลใหม่ ให้เพิ่ม [MEMORY:สรุป] ท้ายข้อความ

== AGENT DECISION ENGINE ==
1. [RESPOND] — ตอบเอง เรื่องที่อยู่ในความเชี่ยวชาญ
2. [ESCALATE:เหตุผล] — แจ้ง CEO ทันที
3. [DELEGATE:ชื่อAgent] — สั่งต่อให้ Agent อื่น
4. [ACT:action] — ดำเนินการ

== ความเชี่ยวชาญ ==
${bot.expertise}

== ทีมงาน ==
S001 พี่วรวัจน์=CEO | S002 พี่เกมส์=IT | S003 พี่ใบแพร=Marketing | S005 พี่ส้ม=Production | S006 พี่แพม=Sales | S007 สจ.โอ=ผู้ประสาน | S008 พี่ดรีม=Admin | S012 พี่อุ้ย=บัญชี | S013 พี่ยุ้ย=รอง CEO

== AI ทีมงาน ==
น้องเลขา (@ExecCopilot) | น้องเซลล์ (@930pchss) | น้องแพร่ (@Aiแพร่) | น้องผลไม้ (@phrae555) | น้องไพลิน (@Jewelry)

== กฎแชทกลุ่ม ==
[type:group] ตอบเมื่อถูกเรียกชื่อ "${bot.name}" หรือเรื่องที่เกี่ยวข้องกับความเชี่ยวชาญ เงียบ [SILENT] เมื่อคนคุยกันเอง
[type:user] ตอบทุกข้อความ

[ข้อความ]
[type:${sourceType}] [groupId:${groupId}] [ผู้ส่ง: ${displayName} | userId: ${userId}]
${messageText}`;
}

// ============================================
// Main Webhook Handler
// ============================================
async function handleWebhook(botKey, events) {
  const bot = BOTS[botKey];
  if (!bot || !bot.channelAccessToken) {
    console.log(`⚠️ Bot "${botKey}" not configured, skipping`);
    return;
  }

  for (const event of events) {
    const startTime = Date.now();

    try {
      // ── Follow Event ──
      if (event.type === 'follow') {
        console.log(`${bot.emoji} [FOLLOW] ${bot.name} — userId: ${event.source.userId}`);

        const now = new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Bangkok' }).replace('T', ' ');

        // Send welcome + save memory (parallel)
        await Promise.all([
          pushMessage(bot.channelAccessToken, event.source.userId, [
            { type: 'text', text: bot.welcome }
          ]),
          saveMemory({
            userId: event.source.userId,
            displayName: 'unknown',
            realName: '', crops: '', area: '', cropStage: '',
            personalNotes: 'New follower',
            lastTopic: 'follow event',
            msgCount: '0',
            firstSeen: now, lastSeen: now,
            oaSource: bot.oaSource
          })
        ]);

        console.log(`${bot.emoji} [FOLLOW] Done in ${Date.now() - startTime}ms`);
        continue;
      }

      // ── Text Message ──
      if (event.type === 'message' && event.message.type === 'text') {
        const userId = event.source.userId;
        console.log(`${bot.emoji} [MSG] ${bot.name} ← "${event.message.text.substring(0, 50)}" from ${userId}`);

        // Step 1: Get LINE profile
        const profile = await getProfile(bot.channelAccessToken, userId).catch(e => {
          console.warn(`⚠️ getProfile failed: ${e.message}`);
          return { displayName: 'ไม่ทราบ' };
        });

        // Step 2: Build prompt and send to Make.com AI Brain
        // (Make.com reads CentralMemory + FarmerMemory + calls Gemini)
        const prompt = buildPrompt(bot, event, profile);
        const aiResponse = await askAIBrain(prompt);

        console.log(`${bot.emoji} [AI] Response: "${aiResponse.substring(0, 80)}..."`);

        // Step 3: Check SILENT (group chat)
        if (isSilent(aiResponse)) {
          console.log(`${bot.emoji} [SILENT] Skipping reply`);
        } else {
          // Step 4: Strip tags and send reply
          const cleanText = stripTags(aiResponse);
          const replyTo = event.source.groupId || event.source.userId;

          if (cleanText) {
            await pushMessage(bot.channelAccessToken, replyTo, [
              { type: 'text', text: cleanText }
            ]);
          }
        }

        // Step 5: Save to FarmerMemory (async — don't wait)
        const memoryTag = extractMemoryTag(aiResponse);
        const now = new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Bangkok' }).replace('T', ' ');

        saveMemory({
          userId,
          displayName: profile.displayName || 'unknown',
          realName: '', crops: '', area: '', cropStage: '',
          personalNotes: memoryTag || '',
          lastTopic: event.message.text.substring(0, 200),
          msgCount: '1',
          firstSeen: now, lastSeen: now,
          oaSource: bot.oaSource
        });

        const elapsed = Date.now() - startTime;
        console.log(`${bot.emoji} [DONE] ${bot.name} processed in ${elapsed}ms`);
      }
    } catch (error) {
      console.error(`❌ [ERROR] ${bot.name}:`, error.message);
    }
  }
}

// ============================================
// Express Routes
// ============================================

// Raw body needed for LINE signature verification
app.use('/webhook', express.raw({ type: '*/*' }));

// Health check
app.get('/', (req, res) => {
  const activeBots = Object.entries(BOTS)
    .filter(([_, b]) => b.channelAccessToken)
    .map(([key, b]) => `${b.emoji} ${b.name} (${b.oaSource})`);

  res.json({
    status: 'ok',
    service: 'AI Fruits Gateway v2.0 Hybrid',
    mode: 'Railway + Make.com Bridge',
    activeBots,
    uptime: Math.floor(process.uptime()) + 's'
  });
});

// Unified webhook endpoint: /webhook/:botId
app.post('/webhook/:botId', async (req, res) => {
  const botId = req.params.botId.toLowerCase();
  const botKey = ROUTE_MAP[botId];

  if (!botKey) {
    console.warn(`⚠️ Unknown botId: ${botId}`);
    return res.status(404).json({ error: `Unknown bot: ${botId}` });
  }

  const bot = BOTS[botKey];

  // Verify LINE signature (if channel secret is configured)
  if (bot.channelSecret) {
    const signature = req.headers['x-line-signature'];
    const bodyStr = req.body.toString('utf-8');

    if (!verifySignature(bot.channelSecret, bodyStr, signature)) {
      console.warn(`⚠️ Invalid signature for ${botKey}`);
      return res.status(401).json({ error: 'Invalid signature' });
    }
  }

  // Parse body
  const bodyStr = req.body.toString('utf-8');
  const body = JSON.parse(bodyStr);
  const events = body.events || [];

  // Return 200 immediately (LINE expects fast response)
  res.status(200).json({ ok: true });

  // Process events asynchronously
  if (events.length > 0) {
    handleWebhook(botKey, events).catch(err => {
      console.error(`❌ Webhook handler error for ${botKey}:`, err);
    });
  }
});

// ============================================
// Start Server
// ============================================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  const activeBots = Object.entries(BOTS)
    .filter(([_, b]) => b.channelAccessToken)
    .map(([_, b]) => `${b.emoji} ${b.name}`);

  console.log(`
╔══════════════════════════════════════════════╗
║   🍊 AI Fruits Gateway v2.0 — Hybrid Mode   ║
╠══════════════════════════════════════════════╣
║  Port: ${String(PORT).padEnd(37)}║
║  Mode: Railway + Make.com Bridge             ║
║  Active Bots: ${String(activeBots.length).padEnd(30)}║
${activeBots.map(b => `║    ${b.padEnd(40)}║`).join('\n')}
║                                              ║
║  Webhook:  /webhook/:botId                   ║
║  Health:   /                                 ║
║  AI Brain: Make.com webhook                  ║
║  Memory:   Make.com webhook                  ║
╚══════════════════════════════════════════════╝
  `);
});

<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ข้อความ Broadcast + แบบฟอร์ม — น้องผลไม้ @phrae555</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@300;400;600;700;800&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Noto Sans Thai',sans-serif; background:#f0fdf4; color:#1a1a1a; }

  /* ===== ส่วนที่ 1: ข้อความแนะนำ + สภาพอากาศ ===== */
  .advisory-section {
    background: linear-gradient(135deg, #047857, #059669);
    color:#fff; padding:24px 20px; text-align:center;
  }
  .advisory-section .emoji-big { font-size:2.5em; margin-bottom:8px; }
  .advisory-section h1 { font-size:1.3em; font-weight:800; line-height:1.4; }
  .advisory-section .subtitle { font-size:0.8em; opacity:0.9; margin-top:4px; }

  .advisory-body {
    max-width:500px; margin:0 auto; padding:20px;
  }
  .advisory-body p {
    font-size:0.88em; color:#374151; line-height:1.8; margin-bottom:12px;
  }

  /* Weather box */
  .weather-alert {
    background:#fef3c7; border:2px solid #f59e0b; border-radius:12px;
    padding:14px; margin:16px 0;
  }
  .weather-alert .wa-title {
    font-size:0.9em; font-weight:700; color:#92400e; margin-bottom:6px;
  }
  .weather-alert .wa-detail {
    font-size:0.82em; color:#78350f; line-height:1.7;
 
# 🤖 ArabBot — نظام بوتين منفصلين

نظام بوتات تيليجرام احترافي مكوّن من بوتين مستقلين يتواصلان عبر REST API داخلي.

---

## 🏗️ هيكل المشروع

```
arabbot/
│
├── shared/                     # كود مشترك بين البوتين
│   ├── config.py               # إعدادات كلا البوتين
│   └── music_bridge.py         # طبقة الاتصال (Admin → Music)
│
├── admin_bot/                  # بوت الإدارة
│   ├── main.py                 # نقطة الانطلاق
│   ├── helpers.py              # دوال مساعدة
│   ├── database.py             # قاعدة البيانات (RAM)
│   └── plugins/
│       ├── moderation.py       # حظر، كتم، طرد، رفع/تنزيل
│       ├── warnings.py         # نظام الإنذارات
│       ├── protection.py       # قفل المحتوى
│       ├── auto_replies.py     # الردود التلقائية
│       ├── welcome.py          # نظام الترحيب
│       ├── music_commands.py   # أوامر الموسيقى ← تُرسَل للـ API
│       └── info.py             # معلومات المستخدم والصور
│
├── music_bot/                  # بوت الموسيقى
│   ├── main.py                 # نقطة الانطلاق (Pyrogram + PyTgCalls + FastAPI)
│   ├── player.py               # محرك التشغيل الصوتي
│   ├── queue_manager.py        # إدارة قوائم الانتظار
│   └── api_server.py           # خادم FastAPI الداخلي
│
├── Dockerfile.admin            # Docker لبوت الإدارة
├── Dockerfile.music            # Docker لبوت الموسيقى
├── docker-compose.yml          # تشغيل البوتين معاً
├── railway.admin.toml          # إعدادات Railway لبوت الإدارة
├── railway.music.toml          # إعدادات Railway لبوت الموسيقى
└── .env.example                # نموذج متغيرات البيئة
```

---

## 🔗 كيف يتواصل البوتان؟

```
المستخدم يكتب: تشغيل أغنية حزينة
        │
        ▼
┌─────────────────┐
│   Admin Bot     │  ← يستقبل الرسالة من تيليجرام
│ (Pyrogram only) │
└────────┬────────┘
         │  POST /play
         │  { chat_id, user_id, query: "أغنية حزينة" }
         │  Header: X-Internal-Secret: xxxxxx
         ▼
┌─────────────────┐
│   Music Bot     │  ← FastAPI يستقبل الطلب
│ FastAPI :8000   │  ← يتحقق من المفتاح السري
└────────┬────────┘  ← yt-dlp يحمّل الأغنية
         │           ← PyTgCalls يشغّلها في Voice Chat
         ▼
   🎵 الصوت يعمل في المجموعة
```

---

## ⚙️ طريقة التشغيل

### 1. إعداد متغيرات البيئة

```bash
cp .env.example .env
# عدّل القيم في .env
```

المتغيرات المطلوبة في `.env`:

| المتغير | الوصف |
|---|---|
| `API_ID` | من my.telegram.org |
| `API_HASH` | من my.telegram.org |
| `ADMIN_BOT_TOKEN` | توكن بوت الإدارة |
| `MUSIC_BOT_TOKEN` | توكن بوت الموسيقى (بوت مختلف!) |
| `MONGO_URL` | رابط MongoDB |
| `SUDO_USERS` | معرفات المشرفين |
| `INTERNAL_SECRET` | مفتاح سري عشوائي (32+ حرف) |

### 2. تشغيل بـ Docker Compose (الأسهل)

```bash
docker-compose up --build -d
```

### 3. تشغيل يدوي (للتطوير)

```bash
# نافذة 1 — بوت الموسيقى أولاً
cd arabbot
pip install -r music_bot/requirements.txt
PYTHONPATH=. python -m music_bot.main

# نافذة 2 — بوت الإدارة
pip install -r admin_bot/requirements.txt
PYTHONPATH=. python -m admin_bot.main
```

---

## 🚀 النشر على Railway

### بوت الإدارة:
1. أنشئ Service جديد في Railway
2. اربطه بالـ repo
3. في إعدادات Build: `Dockerfile Path = Dockerfile.admin`
4. أضف متغيرات البيئة
5. أضف متغير: `MUSIC_API_URL=https://your-music-bot.railway.app`

### بوت الموسيقى:
1. أنشئ Service ثانٍ
2. `Dockerfile Path = Dockerfile.music`
3. أضف متغيرات البيئة (نفس `INTERNAL_SECRET`)
4. ستحصل على URL تضعه في بوت الإدارة كـ `MUSIC_API_URL`

---

## 🎵 مثال كامل: رحلة أمر `تشغيل`

```
1. المستخدم يكتب في المجموعة:
   تشغيل سعد لمجرد - ماشي

2. admin_bot/plugins/music_commands.py يستقبل الرسالة:
   - يستخرج query = "سعد لمجرد - ماشي"
   - يرسل رسالة مؤقتة: "🔍 جاري البحث..."

3. shared/music_bridge.py يرسل HTTP POST:
   POST http://music_bot:8000/play
   Headers: X-Internal-Secret: xxxxx
   Body: { "chat_id": -1001234, "user_id": 99999, "query": "سعد لمجرد - ماشي" }

4. music_bot/api_server.py يستقبل الطلب:
   - يتحقق من المفتاح السري
   - يستدعي player.play(...)

5. music_bot/player.py ينفّذ:
   - yt-dlp يبحث ويحمّل الأغنية → /tmp/music/xxxxx.mp3
   - يضيفها لـ queue_manager
   - PyTgCalls يشغّلها في Voice Chat

6. الـ API يردّ:
   { "ok": true, "title": "سعد لمجرد - ماشي", "position": 1 }

7. Admin Bot يحدّث الرسالة:
   "🎵 جاري تشغيل: سعد لمجرد - ماشي"
```

---

## 📋 أوامر الموسيقى

| الأمر | الوظيفة |
|---|---|
| `تشغيل [اسم الأغنية]` | بحث وتشغيل |
| `ايقاف` | إيقاف وتفريغ القائمة |
| `تخطي` | الأغنية التالية |
| `ايقاف مؤقت` | إيقاف مؤقت |
| `استئناف` | استمرار التشغيل |
| `القائمة` | عرض قائمة الانتظار |

---

## 🔐 الأمان

- الـ API الداخلي يستخدم `X-Internal-Secret` header
- منفذ 8000 لا يُكشف للإنترنت (داخلي فقط بين containers)
- على Railway: استخدم Private Networking بين الـ Services

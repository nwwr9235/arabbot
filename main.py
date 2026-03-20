# main.py - النسخة المتوافقة مع pytgcalls القديمة

import logging
import os
import re
import asyncio
import yt_dlp
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired, UserNotParticipant

# ✅ استيراد المكتبة القديمة (pytgcalls بدون شرطة)
from pytgcalls import GroupCallFactory
from pytgcalls.exceptions import GroupCallNotFoundError

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تهيئة البوت
app = Client(
    "bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# ✅ تهيئة GroupCallFactory للمكتبة القديمة
group_call_factory = GroupCallFactory(app)

# قاعدة بيانات المكالمات النشطة
active_group_calls = {}

# ============================================================
# قواعد البيانات
# ============================================================

group_settings = {}
auto_replies = {}
warnings_db = {}

# قاعدة بيانات الموسيقى
music_queues = {}  # {chat_id: [song_dict, ...]}
current_song = {}  # {chat_id: song_dict}
is_playing = {}    # {chat_id: bool}

def get_group_settings(chat_id):
    if chat_id not in group_settings:
        group_settings[chat_id] = {
            'welcome_enabled': True,
            'welcome_message': 'مرحباً بك {user} في المجموعة {group}!',
            'locks': {
                'links': False,
                'flood': False,
                'spam': False,
                'bots': False,
                'photos': False,
                'videos': False,
                'files': False,
                'stickers': False,
                'voices': False
            }
        }
    return group_settings[chat_id]

async def is_admin(client, chat_id, user_id):
    try:
        if user_id in Config.SUDO_USERS:
            return True
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking admin: {e}")
        return False

async def get_target_from_reply(message):
    """استخراج المستخدم من الرد على الرسالة"""
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        logger.info(f"Target from reply: {target.id} - {target.first_name}")
        return target
    return None

# ============================================================
# نظام الموسيقى - دوال مساعدة
# ============================================================

async def download_song(query):
    """تحميل الأغنية من YouTube"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            url = info.get('webpage_url', '')
            thumbnail = info.get('thumbnail', '')
            
            file_path = ydl.prepare_filename(info)
            ydl.download([url])
            
            return {
                'title': title,
                'file_path': file_path.replace('.webm', '.mp3').replace('.m4a', '.mp3'),
                'duration': duration,
                'url': url,
                'thumbnail': thumbnail
            }
    except Exception as e:
        logger.error(f"Error downloading song: {e}")
        return None

async def play_next_song(client, chat_id):
    """تشغيل الأغنية التالية في القائمة"""
    global music_queues, current_song, is_playing, active_group_calls
    
    if chat_id not in music_queues or not music_queues[chat_id]:
        is_playing[chat_id] = False
        current_song[chat_id] = None
        return
    
    song = music_queues[chat_id].pop(0)
    current_song[chat_id] = song
    is_playing[chat_id] = True
    
    try:
        # ✅ استخدام GroupCallFactory في المكتبة القديمة
        if chat_id not in active_group_calls:
            group_call = group_call_factory.get_group_call()
            active_group_calls[chat_id] = group_call
            await group_call.start(chat_id)
        else:
            group_call = active_group_calls[chat_id]
        
        # تشغيل الملف الصوتي
        await group_call.play_audio(song['file_path'])
        
        await client.send_message(
            chat_id,
            f"🎵 **يتم تشغيل:**\n{song['title']}\n⏱ المدة: {song['duration']//60}:{song['duration']%60:02d}"
        )
        
    except Exception as e:
        logger.error(f"Error playing song: {e}")
        is_playing[chat_id] = False
        await client.send_message(chat_id, f"❌ فشل تشغيل: {str(e)}")

# ============================================================
# أوامر الموسيقى
# ============================================================

@app.on_message(filters.regex(r'^تشغيل\s+(.+)') & filters.group)
async def play_handler(client, message):
    chat_id = message.chat.id
    
    match = re.match(r'^تشغيل\s+(.+)', message.text)
    if not match:
        return await message.reply("⚠️ الصيغة: تشغيل <اسم الأغنية>")
    
    query = match.group(1).strip()
    status_msg = await message.reply("🔍 **جاري البحث...**")
    
    song = await download_song(query)
    
    if not song:
        return await status_msg.edit("❌ **لم يتم العثور على الأغنية**")
    
    if chat_id not in music_queues:
        music_queues[chat_id] = []
    
    music_queues[chat_id].append(song)
    
    await status_msg.edit(f"✅ **تم إضافة إلى القائمة:**\n🎵 {song['title']}")
    
    if not is_playing.get(chat_id, False):
        await play_next_song(client, chat_id)

@app.on_message(filters.regex(r'^تخطي$') & filters.group)
async def skip_handler(client, message):
    chat_id = message.chat.id
    
    if not is_playing.get(chat_id, False):
        return await message.reply("⚠️ **لا يوجد تشغيل حالي**")
    
    try:
        if chat_id in active_group_calls:
            await active_group_calls[chat_id].stop_playout()
        
        await message.reply("⏭ **تم تخطي الأغنية**")
        await asyncio.sleep(1)
        await play_next_song(client, chat_id)
    except Exception as e:
        logger.error(f"Error skipping: {e}")
        await message.reply(f"❌ فشل التخطي: {str(e)}")

@app.on_message(filters.regex(r'^ايقاف$') & filters.group)
async def stop_handler(client, message):
    chat_id = message.chat.id
    
    if not is_playing.get(chat_id, False):
        return await message.reply("⚠️ **لا يوجد تشغيل حالي**")
    
    try:
        if chat_id in active_group_calls:
            await active_group_calls[chat_id].stop()
            del active_group_calls[chat_id]
        
        music_queues[chat_id] = []
        is_playing[chat_id] = False
        current_song[chat_id] = None
        await message.reply("⏹ **تم إيقاف التشغيل**")
    except Exception as e:
        logger.error(f"Error stopping: {e}")
        await message.reply(f"❌ فشل الإيقاف: {str(e)}")

@app.on_message(filters.regex(r'^ايقاف مؤقت$') & filters.group)
async def pause_handler(client, message):
    chat_id = message.chat.id
    
    if not is_playing.get(chat_id, False):
        return await message.reply("⚠️ **لا يوجد تشغيل حالي**")
    
    try:
        if chat_id in active_group_calls:
            await active_group_calls[chat_id].pause_playout()
        await message.reply("⏸ **تم إيقاف مؤقت**")
    except Exception as e:
        logger.error(f"Error pausing: {e}")
        await message.reply(f"❌ فشل: {str(e)}")

@app.on_message(filters.regex(r'^استئناف$') & filters.group)
async def resume_handler(client, message):
    chat_id = message.chat.id
    
    if not is_playing.get(chat_id, False):
        return await message.reply("⚠️ **لا يوجد تشغيل متوقف**")
    
    try:
        if chat_id in active_group_calls:
            await active_group_calls[chat_id].resume_playout()
        await message.reply("▶️ **تم الاستئناف**")
    except Exception as e:
        logger.error(f"Error resuming: {e}")
        await message.reply(f"❌ فشل: {str(e)}")

@app.on_message(filters.regex(r'^قائمة التشغيل$') & filters.group)
async def queue_handler(client, message):
    chat_id = message.chat.id
    
    if chat_id not in music_queues or not music_queues[chat_id]:
        if not current_song.get(chat_id):
            return await message.reply("📭 **قائمة التشغيل فارغة**")
    
    text = "📋 **قائمة التشغيل:**\n\n"
    
    if current_song.get(chat_id):
        text += f"▶️ **الحالية:** {current_song[chat_id]['title']}\n\n"
    
    if chat_id in music_queues:
        for i, song in enumerate(music_queues[chat_id], 1):
            text += f"{i}. {song['title']}\n"
    
    await message.reply(text)

@app.on_message(filters.regex(r'^مغادرة$') & filters.group)
async def leave_handler(client, message):
    chat_id = message.chat.id
    
    try:
        if chat_id in active_group_calls:
            await active_group_calls[chat_id].stop()
            del active_group_calls[chat_id]
        
        music_queues[chat_id] = []
        is_playing[chat_id] = False
        current_song[chat_id] = None
        await message.reply("👋 **تم مغادرة المكالمة**")
    except Exception as e:
        logger.error(f"Error leaving: {e}")
        await message.reply(f"❌ فشل المغادرة: {str(e)}")

# ... باقي الكود (الإدارة، الإنذارات، الردود التلقائية، الحماية، الترحيب) يبقى كما هو ...

# ============================================================
# تشغيل البوت
# ============================================================

if __name__ == "__main__":
    logger.info("🚀 جاري تشغيل البوت...")
    app.run()

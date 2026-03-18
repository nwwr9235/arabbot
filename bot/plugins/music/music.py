"""
bot/plugins/music/music.py
Music player commands in Arabic:
تشغيل، تخطي، ايقاف، ايقاف مؤقت، استئناف، قائمة التشغيل، حذف من القائمة، مغادرة
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database import db_client
from utils import is_admin, mention
from utils.arabic_commands import (
    CMD_PLAY, CMD_SKIP, CMD_STOP, CMD_PAUSE,
    CMD_RESUME, CMD_QUEUE, CMD_REMOVE_QUEUE, CMD_LEAVE_VC
)
from utils.music_player import music_player
from utils.music_downloader import get_track_info
import logging

logger = logging.getLogger(__name__)


def arabic_cmd(cmd: str):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip().startswith(cmd)
    return filters.create(func)


# ── تشغيل ─────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_PLAY) & filters.group)
async def cmd_play(client: Client, message: Message):
    query = message.text.strip()[len(CMD_PLAY):].strip()

    if not query:
        return await message.reply(
            "❗ يرجى كتابة اسم الأغنية أو رابط يوتيوب.\n"
            "مثال: `تشغيل Fairuz`",
            parse_mode="markdown"
        )

    searching_msg = await message.reply("🔍 جاري البحث...")

    track_info = await get_track_info(query)
    if not track_info:
        return await searching_msg.edit("❌ لم يتم العثور على نتائج.")

    track = {
        "title": track_info.get("title", query),
        "url": track_info.get("url", query),
        "duration": track_info.get("duration", "N/A"),
        "thumbnail": track_info.get("thumbnail", ""),
        "channel": track_info.get("channel", "Unknown"),
        "requested_by": message.from_user.id,
        "requested_by_name": message.from_user.first_name,
    }

    await searching_msg.edit(
        f"⬇️ جاري تحميل: **{track['title']}**\nالمدة: `{track['duration']}`",
        parse_mode="markdown"
    )

    result = await music_player.play(message.chat.id, track)

    if result is True:
        await searching_msg.edit(
            f"🎵 **يعزف الآن:**\n"
            f"🎼 {track['title']}\n"
            f"⏱ المدة: `{track['duration']}`\n"
            f"📡 القناة: {track['channel']}\n"
            f"👤 بطلب من: {mention(track['requested_by'], track['requested_by_name'])}",
            parse_mode="markdown"
        )
    elif result is False:
        # Added to queue
        queue = await db_client.get_queue(message.chat.id)
        pos = len(queue)
        await searching_msg.edit(
            f"📋 **تمت الإضافة للقائمة:**\n"
            f"🎼 {track['title']}\n"
            f"📌 الموضع: #{pos}",
            parse_mode="markdown"
        )
    else:
        await searching_msg.edit("❌ فشل في تشغيل الأغنية. تأكد من أن البوت في المحادثة الصوتية.")


# ── تخطي ──────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_SKIP) & filters.group)
async def cmd_skip(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    success = await music_player.skip(message.chat.id)
    if success:
        await message.reply("⏭ تم تخطي الأغنية الحالية.")
    else:
        await message.reply("❌ لا توجد أغنية قيد التشغيل حالياً.")


# ── ايقاف ─────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_STOP) & filters.group)
async def cmd_stop(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    await music_player.stop(message.chat.id)
    await message.reply("⏹ تم إيقاف الموسيقى وتفريغ قائمة التشغيل.")


# ── ايقاف مؤقت ────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_PAUSE) & filters.group)
async def cmd_pause(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    success = await music_player.pause(message.chat.id)
    if success:
        await message.reply("⏸ تم إيقاف التشغيل مؤقتاً.")
    else:
        await message.reply("❌ لا توجد أغنية قيد التشغيل حالياً.")


# ── استئناف ───────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_RESUME) & filters.group)
async def cmd_resume(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    success = await music_player.resume(message.chat.id)
    if success:
        await message.reply("▶️ تم استئناف التشغيل.")
    else:
        await message.reply("❌ لا توجد أغنية موقوفة مؤقتاً.")


# ── قائمة التشغيل ──────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_QUEUE) & filters.group)
async def cmd_queue(client: Client, message: Message):
    current = music_player.get_current(message.chat.id)
    queue = await db_client.get_queue(message.chat.id)

    if not current and not queue:
        return await message.reply("📭 قائمة التشغيل فارغة.")

    text = "🎵 **قائمة التشغيل:**\n\n"

    if current:
        paused = " (موقوف مؤقتاً ⏸)" if music_player.is_paused(message.chat.id) else ""
        text += f"▶️ **الآن يعزف{paused}:**\n"
        text += f"   🎼 {current.get('title', 'Unknown')}\n"
        text += f"   ⏱ {current.get('duration', 'N/A')}\n\n"

    if queue:
        text += "📋 **في الانتظار:**\n"
        for i, track in enumerate(queue[:10], 1):
            text += f"{i}. {track.get('title', 'Unknown')} — `{track.get('duration', 'N/A')}`\n"
        if len(queue) > 10:
            text += f"\n...و {len(queue) - 10} أغنية أخرى"

    await message.reply(text, parse_mode="markdown")


# ── حذف من القائمة ────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_REMOVE_QUEUE) & filters.group)
async def cmd_remove_queue(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    text = message.text.strip()[len(CMD_REMOVE_QUEUE):].strip()
    if not text.isdigit():
        return await message.reply(
            "❗ يرجى تحديد رقم الأغنية في القائمة.\nمثال: `حذف من القائمة 2`",
            parse_mode="markdown"
        )

    index = int(text)
    success = await db_client.remove_from_queue(message.chat.id, index)
    if success:
        await message.reply(f"✅ تم حذف الأغنية رقم {index} من قائمة التشغيل.")
    else:
        await message.reply("❌ الرقم المدخل غير صحيح.")


# ── مغادرة ────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_LEAVE_VC) & filters.group)
async def cmd_leave(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    await music_player.leave(message.chat.id)
    await message.reply("👋 غادرت المحادثة الصوتية.")

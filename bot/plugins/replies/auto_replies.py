"""
bot/plugins/replies/auto_replies.py
Auto-reply system: اضافة رد, حذف رد, عرض الردود
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from database import db_client
from utils import is_admin
from utils.arabic_commands import CMD_ADD_REPLY, CMD_DEL_REPLY, CMD_LIST_REPLIES
import logging

logger = logging.getLogger(__name__)


def arabic_cmd(cmd: str):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip().startswith(cmd)
    return filters.create(func)


@Client.on_message(arabic_cmd(CMD_ADD_REPLY) & filters.group)
async def add_reply(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    text = message.text.strip()
    content = text[len(CMD_ADD_REPLY):].strip()

    if "=" not in content:
        return await message.reply(
            "❗ الصيغة الصحيحة:\n`اضافة رد <الكلمة> = <الرد>`",
            parse_mode="markdown"
        )

    parts = content.split("=", 1)
    trigger = parts[0].strip()
    response = parts[1].strip()

    if not trigger or not response:
        return await message.reply("❗ يرجى تحديد الكلمة والرد.")

    await db_client.add_auto_reply(message.chat.id, trigger, response)
    await message.reply(
        f"✅ تم إضافة الرد التلقائي:\n"
        f"🔑 **الكلمة:** `{trigger}`\n"
        f"💬 **الرد:** {response}",
        parse_mode="markdown"
    )


@Client.on_message(arabic_cmd(CMD_DEL_REPLY) & filters.group)
async def del_reply(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    text = message.text.strip()
    trigger = text[len(CMD_DEL_REPLY):].strip()

    if not trigger:
        return await message.reply("❗ يرجى تحديد الكلمة المراد حذفها.")

    deleted = await db_client.remove_auto_reply(message.chat.id, trigger)
    if deleted:
        await message.reply(f"✅ تم حذف الرد التلقائي للكلمة: `{trigger}`", parse_mode="markdown")
    else:
        await message.reply(f"❌ لا يوجد رد تلقائي للكلمة: `{trigger}`", parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_LIST_REPLIES) & filters.group)
async def list_replies(client: Client, message: Message):
    replies = await db_client.get_auto_replies(message.chat.id)
    if not replies:
        return await message.reply("📭 لا توجد ردود تلقائية في هذه المجموعة.")

    text = "📋 **قائمة الردود التلقائية:**\n\n"
    for i, r in enumerate(replies, 1):
        text += f"{i}. 🔑 `{r['trigger']}` ← {r['response']}\n"

    await message.reply(text, parse_mode="markdown")


@Client.on_message(filters.group & filters.text & ~filters.via_bot, group=2)
async def check_auto_reply(client: Client, message: Message):
    """Check every text message against auto-reply triggers."""
    if not message.text:
        return

    response = await db_client.find_auto_reply(message.chat.id, message.text.strip())
    if response:
        await message.reply(response)

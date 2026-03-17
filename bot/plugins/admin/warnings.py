"""
bot/plugins/admin/warnings.py
Warning system: انذار, عرض الانذارات, مسح الانذارات
Auto-mutes or bans on max warnings.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from database import db_client
from utils import is_admin, extract_user, mention
from utils.arabic_commands import CMD_WARN, CMD_SHOW_WARNS, CMD_CLEAR_WARNS
from config import config
import logging

logger = logging.getLogger(__name__)


def arabic_cmd(cmd: str):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip().startswith(cmd)
    return filters.create(func)


@Client.on_message(arabic_cmd(CMD_WARN) & filters.group)
async def warn_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    if await is_admin(client, message.chat.id, user_id):
        return await message.reply("⚠️ لا يمكن إنذار مشرف.")

    # Extract reason
    text = message.text.strip()
    reason = text[len(CMD_WARN):].strip()
    reason = reason.lstrip("@").strip()
    # Remove mention from reason
    import re
    reason = re.sub(r"@\w+|\d{5,}", "", reason).strip() or "لا يوجد سبب"

    count = await db_client.add_warning(message.chat.id, user_id, reason)
    max_w = config.MAX_WARNINGS

    resp = (
        f"⚠️ **إنذار** لـ {mention(user_id, first_name or str(user_id))}\n"
        f"📝 السبب: {reason}\n"
        f"📊 الإنذارات: {count}/{max_w}"
    )

    if count >= max_w:
        if config.WARN_ACTION == "ban":
            try:
                await client.ban_chat_member(message.chat.id, user_id)
                resp += f"\n\n🚫 تم **حظره** بسبب تجاوز الحد الأقصى للإنذارات."
                await db_client.clear_warnings(message.chat.id, user_id)
            except Exception as e:
                resp += f"\n⚠️ فشل في الحظر: {e}"
        else:
            try:
                await client.restrict_chat_member(
                    message.chat.id,
                    user_id,
                    ChatPermissions(can_send_messages=False)
                )
                resp += f"\n\n🔇 تم **كتمه** بسبب تجاوز الحد الأقصى للإنذارات."
            except Exception as e:
                resp += f"\n⚠️ فشل في الكتم: {e}"

    await message.reply(resp, parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_SHOW_WARNS) & filters.group)
async def show_warns(client: Client, message: Message):
    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        user_id = message.from_user.id
        first_name = message.from_user.first_name

    warns = await db_client.get_warnings(message.chat.id, user_id)
    if not warns:
        return await message.reply(
            f"✅ {mention(user_id, first_name or str(user_id))} لا يملك إنذارات.",
            parse_mode="markdown"
        )

    text = f"📋 **إنذارات** {mention(user_id, first_name or str(user_id))}:\n\n"
    for i, w in enumerate(warns, 1):
        text += f"{i}. {w}\n"
    text += f"\n**المجموع:** {len(warns)}/{config.MAX_WARNINGS}"
    await message.reply(text, parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_CLEAR_WARNS) & filters.group)
async def clear_warns(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    await db_client.clear_warnings(message.chat.id, user_id)
    await message.reply(
        f"✅ تم مسح جميع إنذارات {mention(user_id, first_name or str(user_id))}.",
        parse_mode="markdown"
    )

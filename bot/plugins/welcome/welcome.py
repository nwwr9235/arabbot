"""
bot/plugins/welcome/welcome.py
Welcome system: تفعيل الترحيب, تعطيل الترحيب, تعيين رسالة الترحيب
Sends welcome message when users join.
"""

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from database import db_client
from utils import is_admin, mention
from utils.arabic_commands import (
    CMD_WELCOME_ON, CMD_WELCOME_OFF, CMD_SET_WELCOME
)
import logging

logger = logging.getLogger(__name__)

DEFAULT_WELCOME = (
    "👋 أهلاً وسهلاً {user} في **{group}**!\n"
    "نتمنى لك وقتاً ممتعاً معنا. 🎉"
)


def arabic_cmd(cmd: str):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip().startswith(cmd)
    return filters.create(func)


@Client.on_message(arabic_cmd(CMD_WELCOME_ON) & filters.group)
async def welcome_on(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")
    await db_client.set_welcome(message.chat.id, {"enabled": True})
    await message.reply("✅ تم تفعيل رسالة الترحيب.")


@Client.on_message(arabic_cmd(CMD_WELCOME_OFF) & filters.group)
async def welcome_off(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")
    await db_client.set_welcome(message.chat.id, {"enabled": False})
    await message.reply("✅ تم تعطيل رسالة الترحيب.")


@Client.on_message(arabic_cmd(CMD_SET_WELCOME) & filters.group)
async def set_welcome_msg(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    text = message.text.strip()
    welcome_text = text[len(CMD_SET_WELCOME):].strip()

    if not welcome_text:
        return await message.reply(
            "❗ يرجى كتابة رسالة الترحيب بعد الأمر.\n\n"
            "المتغيرات المتاحة:\n"
            "`{user}` — اسم العضو\n"
            "`{group}` — اسم المجموعة",
            parse_mode="markdown"
        )

    await db_client.set_welcome(message.chat.id, {"message": welcome_text, "enabled": True})
    await message.reply(
        f"✅ تم تعيين رسالة الترحيب:\n\n{welcome_text}",
        parse_mode="markdown"
    )


@Client.on_chat_member_updated(filters.group)
async def greet_new_member(client: Client, update: ChatMemberUpdated):
    """Send welcome message when a new member joins."""
    if not update.new_chat_member:
        return

    # Only trigger on join (not on ban/kick/etc.)
    from pyrogram.enums import ChatMemberStatus
    old_status = update.old_chat_member.status if update.old_chat_member else None
    new_status = update.new_chat_member.status

    if new_status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        return
    if old_status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return

    chat_id = update.chat.id
    welcome_data = await db_client.get_welcome(chat_id)

    if not welcome_data.get("enabled", False):
        return

    user = update.new_chat_member.user
    if user.is_bot:
        return

    welcome_msg = welcome_data.get("message", DEFAULT_WELCOME)
    welcome_msg = welcome_msg.replace("{user}", mention(user.id, user.first_name))
    welcome_msg = welcome_msg.replace("{group}", update.chat.title or "المجموعة")

    try:
        await client.send_message(chat_id, welcome_msg, parse_mode="markdown")
    except Exception as e:
        logger.debug(f"Welcome send error: {e}")

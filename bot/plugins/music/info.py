"""
bot/plugins/info/info.py
Info commands: ايدي, معلوماتي, معلومات, معلومات المجموعة
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatType
from utils import extract_user, mention, is_admin
from utils.arabic_commands import (
    CMD_ID, CMD_MY_INFO, CMD_USER_INFO, CMD_GROUP_INFO
)
import logging

logger = logging.getLogger(__name__)


def arabic_cmd(cmd: str):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip().startswith(cmd)
    return filters.create(func)


# ── ايدي ──────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_ID))
async def cmd_id(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        text = (
            f"🆔 **معرّف المستخدم:**\n"
            f"👤 الاسم: {user.first_name}\n"
            f"🔢 ID: `{user.id}`"
        )
    elif message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        target_text = message.text.strip()[len(CMD_ID):].strip()
        if target_text:
            user_id, first_name = await extract_user(client, message, message.text)
            if user_id:
                text = (
                    f"🆔 **معرّف المستخدم:**\n"
                    f"👤 الاسم: {first_name}\n"
                    f"🔢 ID: `{user_id}`"
                )
            else:
                text = "❌ لم يتم العثور على المستخدم."
        else:
            text = (
                f"🆔 **معرّفاتك:**\n"
                f"👤 اسمك: {message.from_user.first_name}\n"
                f"🔢 ID: `{message.from_user.id}`\n\n"
                f"🏘 **المجموعة:**\n"
                f"📛 الاسم: {message.chat.title}\n"
                f"🔢 ID: `{message.chat.id}`"
            )
    else:
        text = (
            f"🆔 **معرّفك:**\n"
            f"👤 الاسم: {message.from_user.first_name}\n"
            f"🔢 ID: `{message.from_user.id}`"
        )

    await message.reply(text, parse_mode="markdown")


# ── معلوماتي ──────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_MY_INFO))
async def cmd_my_info(client: Client, message: Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "لا يوجد"

    text = (
        f"👤 **معلوماتك الشخصية:**\n\n"
        f"🔢 **ID:** `{user.id}`\n"
        f"📛 **الاسم الأول:** {user.first_name}\n"
        f"📛 **الاسم الأخير:** {user.last_name or 'لا يوجد'}\n"
        f"🔖 **المعرف:** {username}\n"
        f"🤖 **بوت:** {'نعم' if user.is_bot else 'لا'}\n"
        f"✅ **موثق:** {'نعم' if user.is_verified else 'لا'}\n"
        f"🚫 **محظور:** {'نعم' if user.is_restricted else 'لا'}"
    )

    await message.reply(text, parse_mode="markdown")


# ── معلومات @user ─────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_USER_INFO) & ~arabic_cmd(CMD_GROUP_INFO))
async def cmd_user_info(client: Client, message: Message):
    user_id, _ = await extract_user(client, message, message.text)

    if not user_id:
        return await message.reply(
            "❗ يرجى الرد على رسالة أو ذكر المستخدم.\nمثال: `معلومات @username`",
            parse_mode="markdown"
        )

    try:
        user = await client.get_users(user_id)
    except Exception:
        return await message.reply("❌ لم يتم العثور على المستخدم.")

    username = f"@{user.username}" if user.username else "لا يوجد"

    # Check member status if in group
    member_status = "غير معروف"
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        try:
            from pyrogram.enums import ChatMemberStatus
            member = await client.get_chat_member(message.chat.id, user_id)
            status_map = {
                ChatMemberStatus.OWNER: "👑 مالك",
                ChatMemberStatus.ADMINISTRATOR: "⭐ مشرف",
                ChatMemberStatus.MEMBER: "👤 عضو",
                ChatMemberStatus.RESTRICTED: "🔇 مقيد",
                ChatMemberStatus.BANNED: "🚫 محظور",
                ChatMemberStatus.LEFT: "🚪 غادر",
            }
            member_status = status_map.get(member.status, "غير معروف")
        except Exception:
            pass

    text = (
        f"👤 **معلومات المستخدم:**\n\n"
        f"🔢 **ID:** `{user.id}`\n"
        f"📛 **الاسم الأول:** {user.first_name}\n"
        f"📛 **الاسم الأخير:** {user.last_name or 'لا يوجد'}\n"
        f"🔖 **المعرف:** {username}\n"
        f"🤖 **بوت:** {'نعم' if user.is_bot else 'لا'}\n"
        f"✅ **موثق:** {'نعم' if user.is_verified else 'لا'}\n"
        f"📊 **الحالة في المجموعة:** {member_status}"
    )

    await message.reply(text, parse_mode="markdown")


# ── معلومات المجموعة ──────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_GROUP_INFO) & filters.group)
async def cmd_group_info(client: Client, message: Message):
    chat = message.chat

    try:
        full_chat = await client.get_chat(chat.id)
    except Exception:
        full_chat = chat

    members_count = "غير متاح"
    try:
        members_count = f"{await client.get_chat_members_count(chat.id):,}"
    except Exception:
        pass

    username = f"@{full_chat.username}" if full_chat.username else "خاصة"
    description = full_chat.description or "لا يوجد وصف"

    text = (
        f"🏘 **معلومات المجموعة:**\n\n"
        f"📛 **الاسم:** {full_chat.title}\n"
        f"🔢 **ID:** `{full_chat.id}`\n"
        f"🔖 **المعرف:** {username}\n"
        f"👥 **الأعضاء:** {members_count}\n"
        f"📝 **الوصف:** {description[:200]}"
    )

    await message.reply(text, parse_mode="markdown")

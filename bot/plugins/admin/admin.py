"""
bot/plugins/admin/admin.py
Admin moderation commands in Arabic (no slash prefix).
"""

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import (
    UserAdminInvalid, ChatAdminRequired, PeerIdInvalid,
    UserNotParticipant, FloodWait
)
from utils import is_admin, extract_user, mention, is_group
from utils.arabic_commands import (
    CMD_PROMOTE, CMD_DEMOTE, CMD_BAN, CMD_UNBAN,
    CMD_MUTE, CMD_UNMUTE, CMD_KICK, CMD_ADMIN_LIST
)
import asyncio
import logging

logger = logging.getLogger(__name__)

# ── Filters ───────────────────────────────────────────────────────────────────

def arabic_cmd(cmd: str):
    """Filter for Arabic text commands."""
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip().startswith(cmd)
    return filters.create(func)

def arabic_cmd_any(cmds: list):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return any(message.text.strip().startswith(c) for c in cmds)
    return filters.create(func)


# ── Promote ───────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_PROMOTE) & filters.group)
async def promote_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    try:
        await client.promote_chat_member(
            message.chat.id,
            user_id,
            privileges={
                "can_change_info": False,
                "can_post_messages": True,
                "can_edit_messages": False,
                "can_delete_messages": True,
                "can_restrict_members": True,
                "can_invite_users": True,
                "can_pin_messages": True,
            }
        )
        await message.reply(
            f"✅ تمت ترقية {mention(user_id, first_name or str(user_id))} إلى مشرف.",
            parse_mode="markdown"
        )
    except UserAdminInvalid:
        await message.reply("❌ لا يمكن ترقية هذا المستخدم.")
    except ChatAdminRequired:
        await message.reply("❌ البوت لا يملك صلاحيات كافية.")
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Demote ────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_DEMOTE) & filters.group)
async def demote_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    try:
        await client.promote_chat_member(
            message.chat.id,
            user_id,
            privileges={
                "can_change_info": False,
                "can_post_messages": False,
                "can_edit_messages": False,
                "can_delete_messages": False,
                "can_restrict_members": False,
                "can_invite_users": False,
                "can_pin_messages": False,
            }
        )
        await message.reply(
            f"✅ تم تنزيل {mention(user_id, first_name or str(user_id))} من الإدارة.",
            parse_mode="markdown"
        )
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Ban ───────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_BAN) & filters.group)
async def ban_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    if user_id == message.from_user.id:
        return await message.reply("⚠️ لا يمكنك حظر نفسك!")

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await message.reply(
            f"🚫 تم حظر {mention(user_id, first_name or str(user_id))}.",
            parse_mode="markdown"
        )
    except UserAdminInvalid:
        await message.reply("❌ لا يمكن حظر مشرف.")
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Unban ─────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_UNBAN) & filters.group)
async def unban_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    try:
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply(
            f"✅ تم رفع الحظر عن {mention(user_id, first_name or str(user_id))}.",
            parse_mode="markdown"
        )
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Mute ──────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_MUTE) & filters.group)
async def mute_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            )
        )
        await message.reply(
            f"🔇 تم كتم {mention(user_id, first_name or str(user_id))}.",
            parse_mode="markdown"
        )
    except UserAdminInvalid:
        await message.reply("❌ لا يمكن كتم مشرف.")
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Unmute ────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_UNMUTE) & filters.group)
async def unmute_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await message.reply(
            f"🔊 تم إلغاء كتم {mention(user_id, first_name or str(user_id))}.",
            parse_mode="markdown"
        )
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Kick ──────────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd(CMD_KICK) & filters.group)
async def kick_user(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("❌ هذا الأمر للمشرفين فقط.")

    user_id, first_name = await extract_user(client, message, message.text)
    if not user_id:
        return await message.reply("❗ يرجى تحديد المستخدم.")

    try:
        await client.ban_chat_member(message.chat.id, user_id)
        await asyncio.sleep(1)
        await client.unban_chat_member(message.chat.id, user_id)
        await message.reply(
            f"👋 تم طرد {mention(user_id, first_name or str(user_id))} من المجموعة.",
            parse_mode="markdown"
        )
    except UserAdminInvalid:
        await message.reply("❌ لا يمكن طرد مشرف.")
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")


# ── Admin List ────────────────────────────────────────────────────────────────

@Client.on_message(arabic_cmd_any(CMD_ADMIN_LIST) & filters.group)
async def admin_list(client: Client, message: Message):
    try:
        admins = []
        async for member in client.get_chat_members(
            message.chat.id, filter="administrators"
        ):
            if not member.user.is_bot:
                name = member.user.first_name
                user_id = member.user.id
                status = "👑" if member.status == ChatMemberStatus.OWNER else "⭐"
                admins.append(f"{status} {mention(user_id, name)}")

        if not admins:
            return await message.reply("لا يوجد مشرفون.")

        text = "**📋 قائمة المشرفين:**\n\n" + "\n".join(admins)
        await message.reply(text, parse_mode="markdown")
    except Exception as e:
        await message.reply(f"❌ خطأ: {e}")

"""
admin_bot/helpers.py
دوال مساعدة مشتركة بين بلاجن بوت الإدارة
"""

import logging
from pyrogram import Client
from shared.config import AdminConfig

logger = logging.getLogger(__name__)


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """التحقق من صلاحيات الإدارة"""
    try:
        if user_id in AdminConfig.SUDO_USERS:
            return True
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        logger.error(f"is_admin error: {e}")
        return False


async def get_target_from_reply(message):
    """استخراج المستخدم المستهدف من الرد"""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None

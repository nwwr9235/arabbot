# main.py - النسخة المدمجة الكاملة

import logging
import os
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from config import Config

# إعداد الـ Logging
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

# ============================================================
# الأوامر الإدارية - Admin Commands
# ============================================================

@app.on_message(filters.regex(r'^رفع\s+@(\w+)') & filters.group)
async def promote_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.promote_chat_member(
                chat_id=message.chat.id,
                user_id=user.user.id,
                privileges=ChatPermissions(
                    can_change_info=True,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=True,
                    can_manage_chat=True,
                    can_invite_users=True,
                    can_post_messages=True,
                    can_edit_messages=True
                )
            )
            await message.reply(f"✅ تم رفع @{username} إلى رتبة أعلى بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

@app.on_message(filters.regex(r'^تنزيل\s+@(\w+)') & filters.group)
async def demote_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user.user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                )
            )
            await message.reply(f"✅ تم تنزيل @{username} من رتبته بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

@app.on_message(filters.regex(r'^حظر\s+@(\w+)') & filters.group)
async def ban_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.ban_chat_member(message.chat.id, user.user.id)
            await message.reply(f"✅ تم حظر @{username} بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

@app.on_message(filters.regex(r'^الغاء\s+الحظر\s+@(\w+)') & filters.group)
async def unban_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.unban_chat_member(message.chat.id, user.user.id)
            await message.reply(f"✅ تم إلغاء حظر @{username} بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

@app.on_message(filters.regex(r'^كتم\s+@(\w+)') & filters.group)
async def mute_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user.user.id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            await message.reply(f"✅ تم كتم @{username} بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

@app.on_message(filters.regex(r'^الغاء\s+الكتم\s+@(\w+)') & filters.group)
async def unmute_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=user.user.id,
                permissions=ChatPermissions(can_send_messages=True)
            )
            await message.reply(f"✅ تم إلغاء كتم @{username} بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

@app.on_message(filters.regex(r'^طرد\s+@(\w+)') & filters.group)
async def kick_handler(client, message):
    try:
        username = message.matches[0].group(1)
        user = await client.get_chat_member(message.chat.id, username)
        
        if user:
            await client.ban_chat_member(message.chat.id, user.user.id)
            await client.unban_chat_member(message.chat.id, user.user.id)
            await message.reply(f"✅ تم طرد @{username} بنجاح!")
    except Exception as e:
        await message.reply(f"❌ خطأ: {str(e)}")

# ============================================================
# أوامر المساعدة - Help Commands
# ============================================================

@app.on_message(filters.command(["start", "help"]) | filters.regex("^مساعدة$"))
async def help_handler(client, message):
    await message.reply_text("""
🤖 **أوامر البوت:**

**الإدارة:**
رفع @user - رفع المستخدم لرتبة أعلى
تنزيل @user - تنزيل المستخدم من رتبته
حظر @user - حظر المستخدم من المجموعة
الغاء الحظر @user - إلغاء حظر المستخدم
كتم @user - كتم المستخدم
الغاء الكتم @user - إلغاء كتم المستخدم
طرد @user - طرد المستخدم من المجموعة

**الموسيقى:**
تشغيل <الاسم أو الرابط> - تشغيل الموسيقى
تخطي - تخطي الأغنية الحالية
ايقاف - إيقاف التشغيل
ايقاف مؤقت - إيقاف مؤقت
استئناف - استئناف التشغيل

**المعلومات:**
ايدي - عرض معلومات المستخدم
معلومات المجموعة - عرض معلومات المجموعة
    """)

# ============================================================
# تشغيل البوت
# ============================================================

if __name__ == "__main__":
    logger.info("🚀 جاري تشغيل البوت...")
    app.run()

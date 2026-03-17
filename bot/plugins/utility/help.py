"""
bot/plugins/utility/help.py
Help and commands menus in Arabic.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from utils.arabic_commands import (
    CMD_HELP, CMD_COMMANDS, CMD_ADMIN_CMDS,
    CMD_PROTECT_CMDS, CMD_MUSIC_CMDS
)
import logging

logger = logging.getLogger(__name__)


def arabic_cmd(cmd: str):
    async def func(flt, client, message: Message):
        if not message.text:
            return False
        return message.text.strip() == cmd
    return filters.create(func)


HELP_TEXT = """
🤖 **ArabBot — بوت المجموعات العربية**

مرحباً! أنا بوت متكامل لإدارة وحماية وترفيه المجموعات.

📋 **الأوامر المتاحة:**

👮 `الاوامر الادارية` — أوامر الإدارة
🛡 `اوامر الحماية` — أوامر الحماية
🎵 `اوامر الموسيقى` — أوامر المشغل الموسيقي
📋 `الاوامر` — جميع الأوامر

ℹ️ **أوامر المعلومات:**
• `ايدي` — عرض معرّفك
• `معلوماتي` — معلوماتك الشخصية
• `معلومات @user` — معلومات مستخدم
• `معلومات المجموعة` — معلومات المجموعة
"""

ADMIN_CMDS_TEXT = """
👮 **الأوامر الإدارية:**

**الترقية والتنزيل:**
• `رفع @user` — ترقية عضو إلى مشرف
• `تنزيل @user` — إزالة الإشراف

**الحظر:**
• `حظر @user` — حظر مستخدم
• `الغاء الحظر @user` — رفع الحظر

**الكتم:**
• `كتم @user` — كتم مستخدم
• `الغاء الكتم @user` — إلغاء الكتم

**الطرد:**
• `طرد @user` — طرد مستخدم

**قائمة الإدارة:**
• `عرض الادمنية` — عرض قائمة المشرفين
• `قائمة الادمنية` — عرض قائمة المشرفين

**نظام الإنذارات:**
• `انذار @user <سبب>` — إنذار مستخدم
• `عرض الانذارات @user` — عرض إنذارات مستخدم
• `مسح الانذارات @user` — مسح الإنذارات

**الترحيب:**
• `تفعيل الترحيب` — تفعيل رسالة الترحيب
• `تعطيل الترحيب` — تعطيل رسالة الترحيب
• `تعيين رسالة الترحيب <الرسالة>` — تعيين رسالة الترحيب

**الردود التلقائية:**
• `اضافة رد <كلمة> = <رد>` — إضافة رد تلقائي
• `حذف رد <كلمة>` — حذف رد تلقائي
• `عرض الردود` — عرض جميع الردود
"""

PROTECT_CMDS_TEXT = """
🛡 **أوامر الحماية:**

**الروابط:**
• `قفل الروابط` / `فتح الروابط`

**المعرفات:**
• `قفل المعرفات` / `فتح المعرفات`

**البوتات:**
• `قفل البوتات` / `فتح البوتات`

**الصور:**
• `قفل الصور` / `فتح الصور`

**الفيديو:**
• `قفل الفيديو` / `فتح الفيديو`

**الملصقات المتحركة:**
• `قفل المتحركة` / `فتح المتحركة`

**الملفات:**
• `قفل الملفات` / `فتح الملفات`

**الإرسال المتكرر:**
• `قفل التكرار` / `فتح التكرار`

**الرسائل المُعاد توجيهها:**
• `قفل السبام` / `فتح السبام`
"""

MUSIC_CMDS_TEXT = """
🎵 **أوامر الموسيقى:**

**التشغيل:**
• `تشغيل <اسم الأغنية>` — بحث وتشغيل
• `تشغيل <رابط يوتيوب>` — تشغيل رابط مباشر

**التحكم:** *(للمشرفين)*
• `تخطي` — تخطي الأغنية الحالية
• `ايقاف` — إيقاف التشغيل وتفريغ القائمة
• `ايقاف مؤقت` — إيقاف مؤقت
• `استئناف` — استئناف التشغيل
• `مغادرة` — مغادرة المحادثة الصوتية

**قائمة التشغيل:**
• `قائمة التشغيل` — عرض قائمة الأغاني
• `حذف من القائمة <رقم>` — حذف أغنية من القائمة
"""

ALL_CMDS_TEXT = ADMIN_CMDS_TEXT + "\n\n" + PROTECT_CMDS_TEXT + "\n\n" + MUSIC_CMDS_TEXT


@Client.on_message(arabic_cmd(CMD_HELP))
async def cmd_help(client: Client, message: Message):
    await message.reply(HELP_TEXT, parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_COMMANDS))
async def cmd_all_commands(client: Client, message: Message):
    await message.reply(ALL_CMDS_TEXT, parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_ADMIN_CMDS))
async def cmd_admin_commands(client: Client, message: Message):
    await message.reply(ADMIN_CMDS_TEXT, parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_PROTECT_CMDS))
async def cmd_protect_commands(client: Client, message: Message):
    await message.reply(PROTECT_CMDS_TEXT, parse_mode="markdown")


@Client.on_message(arabic_cmd(CMD_MUSIC_CMDS))
async def cmd_music_commands(client: Client, message: Message):
    await message.reply(MUSIC_CMDS_TEXT, parse_mode="markdown")


# Also respond to /start and /help
@Client.on_message(filters.command(["start", "help"]))
async def cmd_start(client: Client, message: Message):
    await message.reply(HELP_TEXT, parse_mode="markdown")

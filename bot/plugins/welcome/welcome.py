# plugins/welcome/welcome.py
import re
from pyrogram import Client, filters
from database.models import GroupSettings

WELCOME_PATTERN = re.compile(r'تفعيل\s+الترحيب|تعطيل\s+الترحيب|تعيين\s+رسالة\s+الترحيب\s+=\s+(.+)')

@app.on_message(filters.new_chat_members & filters.group)
async def welcome_handler(client, message):
    settings = await GroupSettings.get_or_create(message.chat.id)
    
    if not settings.welcome_enabled:
        return
    
    for new_member in message.new_chat_members:
        welcome_text = settings.welcome_message.format(
            user=new_member.first_name,
            group=message.chat.title
        )
        
        await message.reply(welcome_text)

@app.on_message(filters.regex(r'^تفعيل\s+الترحيب') & filters.group)
@is_admin
async def enable_welcome(client, message):
    settings = await GroupSettings.get_or_create(message.chat.id)
    settings.welcome_enabled = True
    await settings.save()
    
    await message.reply("✅ تم تفعيل الترحيب بنجاح!")

@app.on_message(filters.regex(r'^تعطيل\s+الترحيب') & filters.group)
@is_admin
async def disable_welcome(client, message):
    settings = await GroupSettings.get_or_create(message.chat.id)
    settings.welcome_enabled = False
    await settings.save()
    
    await message.reply("✅ تم تعطيل الترحيب بنجاح!")

@app.on_message(filters.regex(r'^تعيين\s+رسالة\s+الترحيب\s+=\s+(.+)') & filters.group)
@is_admin
async def set_welcome(client, message):
    settings = await GroupSettings.get_or_create(message.chat.id)
    settings.welcome_message = message.matches[0].group(1)
    await settings.save()
    
    await message.reply("✅ تم تعيين رسالة الترحيب بنجاح!")

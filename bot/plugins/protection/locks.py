# plugins/protection/locks.py
import re
from pyrogram import Client, filters
from database.models import GroupSettings
from utils.decorators import is_admin

LOCK_PATTERN = re.compile(r'قفل\s+(\w+)')
UNLOCK_PATTERN = re.compile(r'فتح\s+(\w+)')

LOCK_TYPES = {
    'الروابط': 'links',
    'التكرار': 'flood',
    'السبام': 'spam',
    'البوتات': 'bots',
    'الصور': 'photos',
    'الفيديو': 'videos',
    'الملفات': 'files'
}

@app.on_message(filters.regex(r'^قفل\s+(\w+)') & filters.group)
@is_admin
async def lock_handler(client, message):
    lock_type = message.matches[0].group(1)
    
    # Map Arabic to English
    if lock_type in LOCK_TYPES:
        lock_key = LOCK_TYPES[lock_type]
        
        # Update settings
        settings = await GroupSettings.get_or_create(message.chat.id)
        setattr(settings.locks, lock_key, True)
        await settings.save()
        
        await message.reply(f"🔒 تم قفل {lock_type} بنجاح!")
    else:
        await message.reply("⚠️ نوع القفل غير معروف!")

@app.on_message(filters.regex(r'^فتح\s+(\w+)') & filters.group)
@is_admin
async def unlock_handler(client, message):
    lock_type = message.matches[0].group(1)
    
    # Similar logic for unlock
    settings = await GroupSettings.get_or_create(message.chat.id)
    setattr(settings.locks, LOCK_TYPES.get(lock_type, lock_type), False)
    await settings.save()
    
    await message.reply(f"🔓 تم فتح {lock_type} بنجاح!")

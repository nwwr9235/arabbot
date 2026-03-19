# plugins/replies/auto_reply.py
import re
from pyrogram import Client, filters
from database.models import AutoReply

ADD_REPLY_PATTERN = re.compile(r'اضافة\s+رد\s+(\w+)\s+=\s+(.+)')
DELETE_REPLY_PATTERN = re.compile(r'حذف\s+رد\s+(\w+)')
SHOW_REPLIES_PATTERN = re.compile(r'عرض\s+الردود')

@app.on_message(filters.regex(r'^اضافة\s+رد\s+(\w+)\s+=\s+(.+)') & filters.group)
@is_admin
async def add_reply_handler(client, message):
    trigger = message.matches[0].group(1)
    response = message.matches[0].group(2)
    
    # Add to database
    reply = await AutoReply.create(
        trigger=trigger,
        response=response
    )
    
    await message.reply(f"✅ تم إضافة الرد على {trigger} بنجاح!")

@app.on_message(filters.regex(r'^حذف\s+رد\s+(\w+)') & filters.group)
@is_admin
async def delete_reply_handler(client, message):
    trigger = message.matches[0].group(1)
    
    # Delete from database
    reply = await AutoReply.find_one(trigger=trigger)
    if reply:
        await reply.delete()
        await message.reply(f"✅ تم حذف الرد على {trigger} بنجاح!")
    else:
        await message.reply("❌ لم يتم العثور على رد!")

@app.on_message(filters.regex(r'^عرض\s+الردود') & filters.group)
@is_admin
async def show_replies_handler(client, message):
    replies = await AutoReply.find_all()
    
    if replies:
        text = "📋 قائمة الردود:\n\n"
        for reply in replies:
            text += f"• {reply.trigger} -> {reply.response}\n"
        
        await message.reply(text)
    else:
        await message.reply("📭 لا توجد ردود مسجلة!")

@app.on_message(filters.text & filters.group)
async def auto_reply_handler(client, message):
    # Check if message matches any trigger
    replies = await AutoReply.find_all()
    
    for reply in replies:
        if reply.trigger in message.text:
            await message.reply(reply.response)
            break

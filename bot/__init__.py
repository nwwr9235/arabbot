"""
bot/init.py — Compatible with py-tgcalls 2.x
"""

import logging
from pyrogram import Client
from py_tgcalls import PyTgCalls
from config import config

logger = logging.getLogger(name)

class ArabBot(Client):
def init(self):
super().init(
name="arabbot",
api_id=config.API_ID,
api_hash=config.API_HASH,
bot_token=config.BOT_TOKEN,
plugins={"root": "bot/plugins"},
sleep_threshold=30,
workers=64,
)

    # initialize voice client
    self.call_py = PyTgCalls(self)

async def start(self):
    await super().start()

    # start voice calls
    await self.call_py.start()

    # import after start to avoid circular import
    try:
        from utils.music_player import music_player
        music_player.set_pytgcalls(self.call_py)
    except Exception as e:
        logger.warning(f"Music player not loaded: {e}")

    me = await self.get_me()
    logger.info(f"✅ Bot running as @{me.username} ({me.id})")

async def stop(self, *args):
    try:
        await self.call_py.stop()
    except Exception:
        pass

    await super().stop()

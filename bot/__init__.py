"""
bot/__init__.py
Creates the main Pyrogram Client (ArabBot) and loads all plugin modules.
"""

from pyrogram import Client
from pytgcalls import PyTgCalls
from config import config
import importlib
import os
import logging

logger = logging.getLogger(__name__)

PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class ArabBot(Client):
    def __init__(self):
        super().__init__(
            "arabbot_session",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            plugins=dict(root="bot/plugins"),
            sleep_threshold=30,
            workers=64,
        )
        self.pytgcalls = PyTgCalls(self)

    async def start(self):
        await super().start()
        # Wire music_player singleton with this pytgcalls instance
        from utils.music_player import music_player
        music_player.set_pytgcalls(self.pytgcalls)
        await self.pytgcalls.start()
        me = await self.get_me()
        logger.info(f"✅ Bot running as @{me.username} ({me.id})")

    async def stop(self):
        await self.pytgcalls.stop()
        await super().stop()

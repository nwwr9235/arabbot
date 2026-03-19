"""
bot/__init__.py
"""

from pyrogram import Client
from config import config
import logging
import sys

logger = logging.getLogger(__name__)

# ── اكتشاف PyTgCalls ──────────────────────────────────────────────────────────
try:
    from pytgcalls import PyTgCalls
    logger.info("✅ PyTgCalls imported successfully")
except ImportError as e:
    logger.critical(f"❌ Cannot import PyTgCalls: {e}")
    logger.critical(f"pytgcalls content: {__import__('pytgcalls').__dict__.keys()}")
    # نكمل بدون صوت بدلاً من الكراش
    PyTgCalls = None


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
        self.pytgcalls = PyTgCalls(self) if PyTgCalls else None

    async def start(self):
        await super().start()
        if self.pytgcalls:
            from utils.music_player import music_player
            music_player.set_pytgcalls(self.pytgcalls)
            await self.pytgcalls.start()
        else:
            logger.warning("⚠️ Voice chat disabled — PyTgCalls not available")
        me = await self.get_me()
        logger.info(f"✅ Bot running as @{me.username} ({me.id})")

    async def stop(self):
        try:
            if self.pytgcalls:
                await self.pytgcalls.stop()
        except Exception:
            pass
        await super().stop()

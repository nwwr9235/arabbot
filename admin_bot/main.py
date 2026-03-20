"""
admin_bot/main.py
نقطة انطلاق بوت الإدارة
"""

import logging
import importlib
import pkgutil
from pyrogram import Client
from shared.config import AdminConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# تهيئة العميل
# ------------------------------------------------------------------ #
app = Client(
    "admin_bot_session",
    api_id=AdminConfig.API_ID,
    api_hash=AdminConfig.API_HASH,
    bot_token=AdminConfig.BOT_TOKEN,
)

# ------------------------------------------------------------------ #
# تحميل البلاجن تلقائياً
# ------------------------------------------------------------------ #
import admin_bot.plugins as _pkg

for _finder, _name, _ispkg in pkgutil.iter_modules(_pkg.__path__):
    full_name = f"admin_bot.plugins.{_name}"
    module = importlib.import_module(full_name)
    # تسجيل المعالجات إن وجدت دالة register
    if hasattr(module, "register"):
        module.register(app)
    logger.info(f"✅ تم تحميل البلاجن: {full_name}")

# ------------------------------------------------------------------ #
# تشغيل البوت
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    logger.info("🚀 بوت الإدارة يعمل الآن...")
    app.run()

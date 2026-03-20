import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    MONGO_URL = os.getenv("MONGO_URL", "")

    # ✅ تعديل قراءة SUDO_USERS لتقبل الأرقام مفصولة بفاصلة (,) أو مسافات
    sudo_users_str = os.getenv("SUDO_USERS", "")
    if sudo_users_str:
        # استخدام split(",") ثم تنظيف كل جزء من المسافات وتحويله إلى int
        SUDO_USERS = [int(x.strip()) for x in sudo_users_str.split(",") if x.strip()]
    else:
        SUDO_USERS = []

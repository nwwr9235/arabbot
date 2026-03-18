"""
database/__init__.py
MongoDB async client using Motor.  Provides helper classes for every feature.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self):
        # Support both standard and SRV connection strings (Railway MongoDB plugin)
        kwargs = {}
        if config.MONGO_URI.startswith("mongodb+srv://"):
            kwargs["tls"] = True
            kwargs["tlsAllowInvalidCertificates"] = True
        self.client = AsyncIOMotorClient(config.MONGO_URI, **kwargs)
        self.db = self.client[config.DB_NAME]
        # Ping to verify connection
        await self.client.admin.command("ping")
        await self._create_indexes()
        logger.info("✅ MongoDB connected.")

    async def disconnect(self):
        if self.client:
            self.client.close()

    async def _create_indexes(self):
        await self.db.warnings.create_index([("chat_id", 1), ("user_id", 1)])
        await self.db.locks.create_index([("chat_id", 1)], unique=True)
        await self.db.welcome.create_index([("chat_id", 1)], unique=True)
        await self.db.auto_replies.create_index([("chat_id", 1), ("trigger", 1)])
        await self.db.group_settings.create_index([("chat_id", 1)], unique=True)
        await self.db.anti_spam.create_index([("chat_id", 1), ("user_id", 1)])

    # ── Group Settings ────────────────────────────────────────────────────────
    async def get_group_settings(self, chat_id: int) -> dict:
        doc = await self.db.group_settings.find_one({"chat_id": chat_id})
        return doc or {}

    async def update_group_settings(self, chat_id: int, data: dict):
        await self.db.group_settings.update_one(
            {"chat_id": chat_id}, {"$set": data}, upsert=True
        )

    # ── Locks ─────────────────────────────────────────────────────────────────
    async def get_locks(self, chat_id: int) -> dict:
        doc = await self.db.locks.find_one({"chat_id": chat_id})
        return doc.get("locks", {}) if doc else {}

    async def set_lock(self, chat_id: int, lock_name: str, state: bool):
        await self.db.locks.update_one(
            {"chat_id": chat_id},
            {"$set": {f"locks.{lock_name}": state}},
            upsert=True,
        )

    async def is_locked(self, chat_id: int, lock_name: str) -> bool:
        locks = await self.get_locks(chat_id)
        return locks.get(lock_name, False)

    # ── Welcome ───────────────────────────────────────────────────────────────
    async def get_welcome(self, chat_id: int) -> dict:
        doc = await self.db.welcome.find_one({"chat_id": chat_id})
        return doc or {}

    async def set_welcome(self, chat_id: int, data: dict):
        await self.db.welcome.update_one(
            {"chat_id": chat_id}, {"$set": data}, upsert=True
        )

    # ── Warnings ──────────────────────────────────────────────────────────────
    async def get_warnings(self, chat_id: int, user_id: int) -> list:
        doc = await self.db.warnings.find_one(
            {"chat_id": chat_id, "user_id": user_id}
        )
        return doc.get("warns", []) if doc else []

    async def add_warning(self, chat_id: int, user_id: int, reason: str) -> int:
        result = await self.db.warnings.find_one_and_update(
            {"chat_id": chat_id, "user_id": user_id},
            {"$push": {"warns": reason}},
            upsert=True,
            return_document=True,
        )
        return len(result.get("warns", [reason]))

    async def clear_warnings(self, chat_id: int, user_id: int):
        await self.db.warnings.delete_one({"chat_id": chat_id, "user_id": user_id})

    async def count_warnings(self, chat_id: int, user_id: int) -> int:
        doc = await self.db.warnings.find_one(
            {"chat_id": chat_id, "user_id": user_id}
        )
        return len(doc.get("warns", [])) if doc else 0

    # ── Auto Replies ──────────────────────────────────────────────────────────
    async def add_auto_reply(self, chat_id: int, trigger: str, response: str):
        await self.db.auto_replies.update_one(
            {"chat_id": chat_id, "trigger": trigger.lower()},
            {"$set": {"response": response}},
            upsert=True,
        )

    async def remove_auto_reply(self, chat_id: int, trigger: str) -> bool:
        result = await self.db.auto_replies.delete_one(
            {"chat_id": chat_id, "trigger": trigger.lower()}
        )
        return result.deleted_count > 0

    async def get_auto_replies(self, chat_id: int) -> list[dict]:
        cursor = self.db.auto_replies.find({"chat_id": chat_id})
        return await cursor.to_list(length=200)

    async def find_auto_reply(self, chat_id: int, text: str) -> str | None:
        doc = await self.db.auto_replies.find_one(
            {"chat_id": chat_id, "trigger": text.lower().strip()}
        )
        return doc["response"] if doc else None

    # ── Anti Spam (flood) ─────────────────────────────────────────────────────
    async def get_user_messages(self, chat_id: int, user_id: int) -> dict:
        doc = await self.db.anti_spam.find_one({"chat_id": chat_id, "user_id": user_id})
        return doc or {}

    async def update_user_messages(self, chat_id: int, user_id: int, data: dict):
        await self.db.anti_spam.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": data},
            upsert=True,
        )

    # ── Music Queue ───────────────────────────────────────────────────────────
    async def get_queue(self, chat_id: int) -> list:
        doc = await self.db.music_queue.find_one({"chat_id": chat_id})
        return doc.get("queue", []) if doc else []

    async def push_queue(self, chat_id: int, track: dict):
        await self.db.music_queue.update_one(
            {"chat_id": chat_id},
            {"$push": {"queue": track}},
            upsert=True,
        )

    async def pop_queue(self, chat_id: int) -> dict | None:
        doc = await self.db.music_queue.find_one({"chat_id": chat_id})
        if not doc or not doc.get("queue"):
            return None
        track = doc["queue"][0]
        await self.db.music_queue.update_one(
            {"chat_id": chat_id}, {"$pop": {"queue": -1}}
        )
        return track

    async def clear_queue(self, chat_id: int):
        await self.db.music_queue.update_one(
            {"chat_id": chat_id}, {"$set": {"queue": []}}, upsert=True
        )

    async def remove_from_queue(self, chat_id: int, index: int) -> bool:
        queue = await self.get_queue(chat_id)
        if index < 1 or index > len(queue):
            return False
        queue.pop(index - 1)
        await self.db.music_queue.update_one(
            {"chat_id": chat_id}, {"$set": {"queue": queue}}, upsert=True
        )
        return True


db_client = Database()

# database/db.py
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

client: Optional[AsyncIOMotorClient] = None

async def get_client():
    global client
    if client is None:
        client = AsyncIOMotorClient("mongodb://localhost:27017")
    return client

async def get_database():
    client = await get_client()
    return client.telegram_bot

async def close_client():
    if client:
        client.close()


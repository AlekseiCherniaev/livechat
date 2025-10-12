from typing import Any

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase


async def ensure_indexes(db: AsyncDatabase[Any]) -> None:
    users = db["users"]
    await users.create_index([("username", ASCENDING)], unique=True)
    await users.create_index([("last_active_at", ASCENDING)])

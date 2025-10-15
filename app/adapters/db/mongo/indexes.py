from typing import Any

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase


async def ensure_indexes(db: AsyncDatabase[Any]) -> None:
    users = db["users"]
    await users.create_index([("username", ASCENDING)], unique=True)

    rooms = db["rooms"]
    await rooms.create_index([("name", ASCENDING)], unique=True)
    await rooms.create_index([("participants_count", ASCENDING)])

    room_memberships = db["room_memberships"]
    await room_memberships.create_index(
        [("room_id", ASCENDING), ("user_id", ASCENDING)], unique=True
    )

    notifications = db["notifications"]
    await notifications.create_index([("user_id", ASCENDING)])
    await notifications.create_index([("created_at", ASCENDING)])
    await notifications.create_index([("read", ASCENDING)])

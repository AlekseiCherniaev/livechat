from typing import Any

import structlog
from pymongo import ASCENDING
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


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

    join_requests = db["join_requests"]
    await join_requests.create_index(
        [("room_id", ASCENDING), ("user_id", ASCENDING)], unique=True
    )
    await join_requests.create_index([("status", ASCENDING)])


async def create_mongo_client() -> AsyncMongoClient[Any]:
    client: AsyncMongoClient[Any] = AsyncMongoClient(get_settings().mongo_uri)
    await ensure_indexes(db=client[get_settings().mongo_dbname])
    logger.info("MongoDB connected and indexes ensured")
    return client

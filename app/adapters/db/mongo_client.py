from typing import Any

import structlog
from pymongo import AsyncMongoClient

from app.adapters.db.mongo.indexes import ensure_indexes
from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


async def create_mongo_client() -> AsyncMongoClient[Any]:
    client: AsyncMongoClient[Any] = AsyncMongoClient(get_settings().mongo_uri)
    await ensure_indexes(db=client[get_settings().mongo_dbname])
    logger.info("MongoDB connected and indexes ensured")
    return client

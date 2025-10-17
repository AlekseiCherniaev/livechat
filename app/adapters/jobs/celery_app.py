from typing import Any

from celery import Celery
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis

from app.adapters.db.mongo_client import create_mongo_client
from app.core.settings import get_settings

celery_app = Celery(
    "outbox_worker",
    broker=get_settings().redis_celery_broker_dsn,
    backend=get_settings().redis_celery_backend_dsn,
)

celery_app.conf.beat_schedule = {
    "run-outbox-repair-every-minute": {
        "task": "app.jobs.tasks.run_outbox_repair",
        "schedule": get_settings().celery_schedule,
    },
}
celery_app.conf.timezone = "UTC"

redis_client: Redis | None = None
mongo_client: AsyncMongoClient[Any] | None = None
mongo_db: AsyncDatabase[Any] | None = None


async def get_redis_client():
    global redis_client
    if not redis_client:
        redis_client = Redis.from_url(get_settings().redis_celery_backend_dsn)
    return redis_client


async def get_mongo_db():
    global mongo_db, mongo_client
    if not mongo_client:
        mongo_client = await create_mongo_client()
    if not mongo_db:
        mongo_db = mongo_client[get_settings().mongo_dbname]
    return mongo_db

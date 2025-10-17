import asyncio
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


@celery_app.on_after_finalize.connect
def init_clients(sender, **kwargs):
    global redis_client, mongo_client, mongo_db

    loop = asyncio.get_event_loop()
    redis_client = Redis.from_url(get_settings().redis_celery_backend_dsn)
    mongo_client = loop.run_until_complete(create_mongo_client())
    mongo_db = mongo_client[get_settings().mongo_dbname]

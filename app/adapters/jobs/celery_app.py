import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from celery import Celery
from clickhouse_connect.driver.asyncclient import AsyncClient
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis
from redis.exceptions import LockError

from app.adapters.analytics.analytics import ClickHouseAnalyticsRepository
from app.adapters.analytics.clickhouse_client import create_clickhouse_client
from app.adapters.connection.redis_connection import RedisConnectionPort
from app.adapters.db.cassandra_engine import CassandraEngine
from app.adapters.db.mongo_client import create_mongo_client
from app.adapters.db.repos.cassandra.message import CassandraMessageRepository
from app.adapters.db.repos.mongo.notification import MongoNotificationRepository
from app.adapters.db.repos.mongo.outbox import MongoOutboxRepository
from app.adapters.jobs.outbox_repair import OutboxRepairJob
from app.adapters.notification_sender.websocket_sender import (
    WebSocketNotificationSender,
)
from app.core.constants import AnalyticsEventType, NotificationType, OutboxMessageType
from app.core.settings import get_settings
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.notification import Notification

logger = structlog.get_logger(__name__)

# TODO replace with https://github.com/python-arq/arq
celery_app = Celery(
    "outbox_worker",
    broker=get_settings().redis_celery_broker_dsn,
    backend=get_settings().redis_celery_backend_dsn,
)

celery_app.conf.beat_schedule = {
    "run-outbox-repair-every-minute": {
        "task": "app.jobs.tasks.run_outbox_repair_sync",
        "schedule": get_settings().celery_schedule,
    },
    "process-outbox-every-minute": {
        "task": "app.jobs.tasks.process_outbox_sync",
        "schedule": get_settings().celery_schedule,
    },
}
celery_app.conf.timezone = "UTC"
celery_app.conf.task_always_eager = False
celery_app.conf.worker_pool = "solo"
celery_app.conf.worker_concurrency = 1

cassandra_connection = CassandraEngine()


def run_async[T](func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(func(*args, **kwargs))


@asynccontextmanager
async def get_redis_context() -> AsyncGenerator[Redis, None]:
    redis = Redis.from_url(get_settings().redis_celery_backend_dsn)
    try:
        yield redis
    finally:
        await redis.close()


@asynccontextmanager
async def get_mongo_context() -> AsyncGenerator[AsyncDatabase[Any], None]:
    client = await create_mongo_client()
    try:
        yield client[get_settings().mongo_dbname]
    finally:
        await client.close()


@asynccontextmanager
async def get_clickhouse_context() -> AsyncGenerator[AsyncClient, None]:
    client = await create_clickhouse_client()
    try:
        yield client
    finally:
        await client.close()  # type:ignore[no-untyped-call]


@celery_app.task(
    name="app.jobs.tasks.process_outbox_sync",
    max_retries=3,
    default_retry_delay=30,
)
def process_outbox_sync() -> None:
    run_async(process_outbox)


@celery_app.task(
    name="app.jobs.tasks.run_outbox_repair_sync",
    max_retries=3,
    default_retry_delay=30,
)
def run_outbox_repair_sync() -> None:
    run_async(run_outbox_repair)


async def run_outbox_repair() -> None:
    try:
        async with (
            get_redis_context() as redis_client,
            get_mongo_context() as mongo_db,
            redis_client.lock(
                get_settings().celery_redis_repair_lock_key,
                timeout=get_settings().celery_redis_repair_lock_key_timeout,
                blocking=False,
            ),
        ):
            logger.info("Acquired lock, starting OutboxRepairJob")

            message_repo = CassandraMessageRepository()
            outbox_repo = MongoOutboxRepository(db=mongo_db)
            job = OutboxRepairJob(message_repo, outbox_repo)

            await job.run_once()

            logger.info("OutboxRepairJob completed")

    except LockError:
        logger.warning("OutboxRepairJob already running, skipping this run")


async def process_outbox() -> None:
    try:
        async with (
            get_redis_context() as redis_client,
            get_mongo_context() as mongo_db,
            get_clickhouse_context() as clickhouse_client,
            redis_client.lock(
                get_settings().celery_redis_worker_lock_key,
                timeout=get_settings().celery_redis_worker_lock_key_timeout,
                blocking=False,
            ),
        ):
            logger.info("Acquired lock, starting processing outbox")
            outbox_repo = MongoOutboxRepository(db=mongo_db)
            notification_repo = MongoNotificationRepository(db=mongo_db)
            analytics_port = ClickHouseAnalyticsRepository(client=clickhouse_client)
            notification_sender = WebSocketNotificationSender(
                connection_port=RedisConnectionPort(redis=redis_client)
            )

            pending = await outbox_repo.list_pending(limit=100)
            for outbox in pending:
                task_logger = logger.bind(outbox_id=outbox.id, type=outbox.type.value)
                await outbox_repo.mark_in_progress(outbox_id=outbox.id)
                try:
                    payload = outbox.payload
                    logger.bind(outbox_id=str(outbox.id), payload=payload).debug(
                        "Processing outbox with given payload"
                    )
                    if outbox.type == OutboxMessageType.NOTIFICATION:
                        notification = Notification(
                            user_id=UUID(payload.get("user_id")),
                            payload=payload.get("payload", {}),
                            read=payload.get("read", False),
                            source_id=payload.get("source_id")
                            and UUID(payload.get("source_id")),
                            id=UUID(payload.get("id")),
                            type=NotificationType(payload.get("type")),
                        )
                        await notification_repo.save(notification)
                        await notification_sender.send(notification)
                        task_logger.info("Notification sent successfully")

                    elif outbox.type == OutboxMessageType.ANALYTICS:
                        event = AnalyticsEvent(
                            event_type=AnalyticsEventType(payload.get("event_type")),
                            user_id=payload.get("user_id")
                            and UUID(payload.get("user_id")),
                            room_id=payload.get("room_id")
                            and UUID(payload.get("room_id")),
                            payload=payload.get("payload") or {},
                            id=UUID(payload.get("id")),
                        )
                        await analytics_port.publish_event(event)
                        task_logger.info("Analytics event published successfully")

                    await outbox_repo.mark_sent(
                        outbox_id=outbox.id, sent_at=datetime.now(UTC)
                    )
                    task_logger.info("Outbox marked as SENT")
                except Exception as e:
                    if outbox.retries + 1 >= outbox.max_retries:
                        await outbox_repo.mark_failed(outbox_id=outbox.id, error=str(e))
                        task_logger.bind(e=str(e)).error(
                            "Outbox item failed permanently"
                        )
                    else:
                        await outbox_repo.mark_pending(
                            outbox_id=outbox.id,
                            retry=True,
                            last_error=str(e),
                        )
                        task_logger.bind(e=str(e)).warning("Outbox item will retry")

            logger.info("Processing outbox completed")

    except LockError:
        logger.warning("OutboxWorker already running, skipping this run")

from datetime import datetime, timezone
from uuid import UUID

import structlog
from redis.exceptions import LockError

from app.adapters.db.repos.cassandra.message import CassandraMessageRepository
from app.adapters.db.repos.mongo.notification import MongoNotificationRepository
from app.adapters.db.repos.mongo.outbox import MongoOutboxRepository
from app.adapters.jobs.celery_app import celery_app, get_mongo_db, get_redis_client
from app.adapters.jobs.outbox_repair import OutboxRepairJob
from app.core.constants import OutboxMessageType, NotificationType, AnalyticsEventType
from app.core.settings import get_settings
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.notification import Notification
from app.domain.ports.analytics import AnalyticsPort
from app.domain.ports.notification_sender import NotificationSenderPort

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.jobs.tasks.run_outbox_repair",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
async def run_outbox_repair():
    try:
        redis_client = await get_redis_client()
        mongo_db = await get_mongo_db()
        async with redis_client.lock(
            get_settings().celery_redis_lock_key,
            timeout=get_settings().celery_redis_lock_key_timeout,
            blocking=False,
        ):
            logger.info("Acquired lock, starting OutboxRepairJob")

            message_repo = CassandraMessageRepository()
            outbox_repo = MongoOutboxRepository(db=mongo_db)
            job = OutboxRepairJob(message_repo, outbox_repo)

            await job.run_once()

            logger.info("OutboxRepairJob completed")

    except LockError:
        logger.warning("OutboxRepairJob already running, skipping this run")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
async def process_outbox():
    try:
        redis_client = await get_redis_client()
        mongo_db = await get_mongo_db()
        logger.info("Acquired lock, starting processing outbox")
        async with redis_client.lock(
            get_settings().celery_redis_worker_lock_key,
            timeout=get_settings().celery_redis_worker_lock_key_timeout,
            blocking=False,
        ):
            outbox_repo = MongoOutboxRepository(db=mongo_db)
            notification_repo = MongoNotificationRepository(db=mongo_db)
            analytics_port = AnalyticsPort()
            notification_sender = NotificationSenderPort()

            pending = await outbox_repo.list_pending(limit=100)
            for outbox in pending:
                task_logger = logger.bind(
                    outbox_id=str(outbox.id), type=outbox.type.value
                )
                await outbox_repo.mark_in_progress(outbox_id=outbox.id)
                try:
                    if outbox.type == OutboxMessageType.NOTIFICATION:
                        payload = outbox.payload
                        notification = Notification(
                            user_id=UUID(payload.get("user_id")),
                            payload=payload.get("payload"),
                            read=payload.get("read"),
                            source_id=UUID(payload.get("source_id")),
                            id=UUID(payload.get("id")),
                            type=NotificationType(payload.get("type")),
                        )
                        await notification_repo.save(notification)
                        await notification_sender.send(notification)
                        task_logger.info("Notification sent successfully")

                    elif outbox.type == OutboxMessageType.ANALYTICS:
                        payload = outbox.payload
                        event = AnalyticsEvent(
                            event_type=AnalyticsEventType(payload.get("event_type")),
                            user_id=UUID(payload.get("user_id")),
                            room_id=UUID(payload.get("room_id")),
                            payload=payload.get("payload"),
                            id=UUID(payload.get("id")),
                        )
                        await analytics_port.publish_event(event)
                        task_logger.info("Analytics event published successfully")

                    await outbox_repo.mark_sent(
                        outbox_id=outbox.id, sent_at=datetime.now(timezone.utc)
                    )
                    task_logger.info("Outbox marked as SENT")
                except Exception as e:
                    if outbox.retries + 1 >= outbox.max_retries:
                        await outbox_repo.mark_failed(outbox_id=outbox.id, error=str(e))
                        task_logger.error("Outbox item failed permanently")
                    else:
                        await outbox_repo.mark_in_progress(
                            outbox_id=outbox.id, retry=True
                        )
                        task_logger.warning("Outbox item will retry")

            logger.info("Processing outbox completed")

    except LockError:
        logger.warning("OutboxWorker already running, skipping this run")

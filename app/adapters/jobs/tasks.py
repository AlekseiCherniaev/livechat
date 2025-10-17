import structlog
from redis.exceptions import LockError

from app.adapters.db.repos.cassandra.message import CassandraMessageRepository
from app.adapters.db.repos.mongo.outbox import MongoOutboxRepository
from app.adapters.jobs.celery_app import celery_app, redis_client, mongo_db
from app.adapters.jobs.outbox_repair import OutboxRepairJob
from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.jobs.tasks.run_outbox_repair",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
async def run_outbox_repair():
    try:
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

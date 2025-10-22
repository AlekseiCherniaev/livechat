import asyncio
from datetime import UTC, datetime, timedelta

import structlog

from app.core.constants import AnalyticsEventType, OutboxMessageType, OutboxStatus
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.outbox import Outbox
from app.domain.repos.message import MessageRepository
from app.domain.repos.outbox import OutboxRepository

logger = structlog.get_logger(__name__)


class OutboxRepairJob:
    dedup_mapping = (
        ("message_sent", AnalyticsEventType.MESSAGE_SENT),
        ("message_deleted", AnalyticsEventType.MESSAGE_DELETED),
        ("message_edited", AnalyticsEventType.MESSAGE_EDITED),
    )

    def __init__(
        self,
        message_repo: MessageRepository,
        outbox_repo: OutboxRepository,
        window_minutes: int = 3,
        batch_size: int = 200,
        delay_between_batches: float = 0.1,
    ):
        self._message_repo = message_repo
        self._outbox_repo = outbox_repo
        self._window_minutes = window_minutes
        self._batch_size = batch_size
        self._delay_between_batches = delay_between_batches

    async def run_once(self) -> None:
        since = datetime.now(UTC) - timedelta(minutes=self._window_minutes)
        logger.bind(since=str(since)).info("Starting OutboxRepairJob")

        repaired = 0
        start_after = None

        while True:
            try:
                messages = await self._message_repo.get_since_all_rooms(
                    since=since, limit=self._batch_size, start_after=start_after
                )
            except Exception as e:
                logger.bind(error=str(e)).exception(
                    "Failed to fetch messages from repository"
                )
                break

            if not messages:
                break

            all_keys: list[str] = []
            for msg in messages:
                all_keys.extend(
                    (
                        f"message_sent:{msg.id}",
                        f"message_deleted:{msg.id}",
                        f"message_edited:{msg.id}",
                    )
                )

            try:
                existing_keys = set(
                    await self._outbox_repo.exists_by_dedup_keys(all_keys)
                )
            except Exception as e:
                logger.bind(error=str(e)).exception(
                    "Failed to check existing outbox keys"
                )
                existing_keys = set()

            for msg in messages:
                for prefix, event_type in OutboxRepairJob.dedup_mapping:
                    dedup_key = f"{prefix}:{msg.id}"
                    if dedup_key in existing_keys:
                        continue

                    try:
                        analytics = AnalyticsEvent(
                            event_type=event_type,
                            user_id=msg.user_id,
                            room_id=msg.room_id,
                            payload={"message": msg.content},
                        )
                        outbox = Outbox(
                            type=OutboxMessageType.ANALYTICS,
                            status=OutboxStatus.PENDING,
                            payload=analytics.to_payload(),
                            dedup_key=dedup_key,
                        )
                        await self._outbox_repo.save(outbox=outbox)
                        repaired += 1

                    except Exception as e:
                        logger.bind(
                            message_id=msg.id, dedup_key=dedup_key, error=str(e)
                        ).exception("Failed to repair outbox event")

            await asyncio.sleep(self._delay_between_batches)

            last_msg = messages[-1]
            start_after = (last_msg.created_at, last_msg.id)
            if len(messages) < self._batch_size:
                break

        logger.bind(repaired=repaired).info("Outbox repair completed")

    async def run_forever(self, interval_seconds: int = 60) -> None:
        while True:
            try:
                await self.run_once()
            except Exception as e:
                logger.bind(error=str(e)).exception("Outbox repair job failed")
            await asyncio.sleep(interval_seconds)

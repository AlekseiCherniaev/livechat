from uuid import UUID

import structlog

from app.core.constants import AnalyticsEventType
from app.domain.entities.notification import Notification
from app.domain.exceptions.notification import NotificationNotFound
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.notification import NotificationRepository
from app.domain.repos.outbox_event import OutboxEventRepository
from app.domain.services.utils import create_outbox_analytics_event

logger = structlog.get_logger(__name__)


class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        outbox_repo: OutboxEventRepository,
        transaction_manager: TransactionManager,
    ) -> None:
        self._notif_repo = notification_repo
        self._outbox_repo = outbox_repo
        self._tm = transaction_manager

    async def list_user_notifications(
        self, user_id: UUID, unread_only: bool = False
    ) -> list[Notification]:
        notifications = await self._notif_repo.get_user_notifications(
            user_id=user_id, unread_only=unread_only
        )
        logger.bind(user_id=user_id).debug(
            f"Fetched {len(notifications)} notifications (unread_only={unread_only})"
        )
        return notifications

    async def mark_as_read(self, notification_id: UUID) -> None:
        notification = await self._notif_repo.get(notification_id=notification_id)
        if notification is None:
            raise NotificationNotFound

        async def _txn():
            await self._notif_repo.mark_as_read(notification_id)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.NOTIFICATION_READ,
                payload=notification.payload,
                dedup_key=f"notif_read:{notification_id}",
            )

            logger.bind(notification_id=notification_id).info(
                "Notification marked as read"
            )

        await self._tm.run_in_transaction(_txn)

    async def mark_all_as_read(self, user_id: UUID) -> None:
        async def _txn():
            await self._notif_repo.mark_all_as_read(user_id)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.NOTIFICATIONS_ALL_READ,
                user_id=user_id,
                dedup_key=f"notif_all_read:{user_id}",
            )

            logger.bind(user_id=user_id).info("All notifications marked as read")

        await self._tm.run_in_transaction(_txn)

    async def count_unread(self, user_id: UUID) -> int:
        count = await self._notif_repo.count_unread(user_id)
        logger.bind(user_id=user_id, unread_count=count).debug(
            "Fetched unread notification count"
        )
        return count

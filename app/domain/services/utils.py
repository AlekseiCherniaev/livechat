from uuid import UUID

from app.core.constants import (
    AnalyticsEventType,
    OutboxMessageType,
    OutboxStatus,
    NotificationType,
)
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.notification import Notification
from app.domain.entities.outbox_event import OutboxEvent
from app.domain.repos.outbox_event import OutboxEventRepository


async def create_outbox_analytics_event(
    outbox_repo: OutboxEventRepository,
    event_type: AnalyticsEventType,
    user_id: UUID | None = None,
    room_id: UUID | None = None,
    payload: dict | None = None,
    dedup_key: str | None = None,
) -> None:
    analytics = AnalyticsEvent(
        event_type=event_type,
        user_id=user_id,
        room_id=room_id,
        payload=payload,
    )
    outbox = OutboxEvent(
        type=OutboxMessageType.ANALYTICS,
        status=OutboxStatus.PENDING,
        payload=analytics.to_payload(),
        dedup_key=dedup_key,
    )
    await outbox_repo.save(outbox)


async def create_outbox_notification_event(
    outbox_repo: OutboxEventRepository,
    notification_type: NotificationType,
    user_id: UUID,
    source_id: UUID | None = None,
    payload: dict | None = None,
    dedup_key: str | None = None,
) -> None:
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        payload=payload,
        source_id=source_id,
    )
    notif_out = OutboxEvent(
        type=OutboxMessageType.NOTIFICATION,
        status=OutboxStatus.PENDING,
        payload=notif.to_payload(),
        dedup_key=dedup_key,
    )
    await outbox_repo.save(notif_out)

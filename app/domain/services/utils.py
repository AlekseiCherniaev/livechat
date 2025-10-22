from typing import Any
from uuid import UUID

from app.core.constants import (
    AnalyticsEventType,
    NotificationType,
    OutboxMessageType,
    OutboxStatus,
)
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.notification import Notification
from app.domain.entities.outbox import Outbox
from app.domain.repos.outbox import OutboxRepository


async def create_outbox_analytics_event(
    outbox_repo: OutboxRepository,
    event_type: AnalyticsEventType,
    user_id: UUID | None = None,
    room_id: UUID | None = None,
    payload: dict[str, str] | None = None,
    dedup_key: str | None = None,
    db_session: Any | None = None,
) -> None:
    analytics = AnalyticsEvent(
        event_type=event_type,
        user_id=user_id,
        room_id=room_id,
        payload=payload,
    )
    outbox = Outbox(
        type=OutboxMessageType.ANALYTICS,
        status=OutboxStatus.PENDING,
        payload=analytics.to_payload(),
        dedup_key=dedup_key,
    )
    await outbox_repo.save(outbox=outbox, db_session=db_session)


async def create_outbox_notification_event(
    outbox_repo: OutboxRepository,
    notification_type: NotificationType,
    user_id: UUID,
    payload: dict[str, str],
    source_id: UUID | None = None,
    dedup_key: str | None = None,
    db_session: Any | None = None,
) -> None:
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        payload=payload,
        source_id=source_id,
    )
    outbox = Outbox(
        type=OutboxMessageType.NOTIFICATION,
        status=OutboxStatus.PENDING,
        payload=notif.to_payload(),
        dedup_key=dedup_key,
    )
    await outbox_repo.save(outbox=outbox, db_session=db_session)

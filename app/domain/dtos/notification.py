from dataclasses import dataclass
from uuid import UUID

from app.core.constants import NotificationType
from app.domain.entities.notification import Notification


@dataclass
class NotificationPublicDTO:
    type: NotificationType
    payload: dict[str, str]
    read: bool
    source_id: UUID | None
    id: UUID


def notification_to_dto(notification: Notification) -> NotificationPublicDTO:
    return NotificationPublicDTO(
        type=notification.type,
        payload=notification.payload,
        read=notification.read,
        source_id=notification.source_id,
        id=notification.id,
    )

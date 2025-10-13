from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.constants import NotificationType
from app.domain.entities.notification import Notification


def notification_to_document(notification: Notification) -> dict[str, Any]:
    return {
        "_id": str(notification.id),
        "user_id": str(notification.user_id),
        "type": notification.type.value,
        "created_at": notification.created_at,
        "payload": notification.payload,
        "read": notification.read,
    }


def document_to_notification(doc: dict[str, Any]) -> Notification:
    return Notification(
        id=UUID(doc["_id"]),
        user_id=UUID(doc["user_id"]),
        type=NotificationType(doc["type"]),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        payload=doc.get("payload"),
        read=doc.get("read", False),
    )

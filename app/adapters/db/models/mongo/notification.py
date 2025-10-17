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
        "payload": notification.payload,
        "read": notification.read,
        "source_id": notification.source_id and str(notification.source_id),
        "created_at": notification.created_at,
        "updated_at": notification.updated_at,
    }


def document_to_notification(doc: dict[str, Any]) -> Notification:
    return Notification(
        id=UUID(doc["_id"]),
        user_id=UUID(doc["user_id"]),
        type=NotificationType(doc["type"]),
        payload=doc.get("payload", {}),
        read=doc.get("read", False),
        source_id=doc.get("source_id") and UUID(doc.get("source_id")),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.constants import OutboxStatus, OutboxMessageType
from app.domain.entities.outbox import Outbox


def outbox_to_document(outbox: Outbox) -> dict[str, Any]:
    return {
        "_id": str(outbox.id),
        "type": outbox.type.value,
        "status": outbox.status.value,
        "payload": outbox.payload,
        "dedup_key": outbox.dedup_key,
        "retries": outbox.retries,
        "max_retries": outbox.max_retries,
        "sent_at": outbox.sent_at,
        "last_error": outbox.last_error,
        "created_at": outbox.created_at,
    }


def document_to_outbox(doc: dict[str, Any]) -> Outbox:
    return Outbox(
        id=UUID(doc["_id"]),
        type=OutboxMessageType(doc["type"]),
        status=OutboxStatus(doc["status"]),
        payload=doc.get("payload", {}),
        dedup_key=doc.get("dedup_key"),
        retries=doc.get("retries", 0),
        max_retries=doc.get("max_retries", 5),
        sent_at=doc.get("sent_at"),
        last_error=doc.get("last_error"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
    )

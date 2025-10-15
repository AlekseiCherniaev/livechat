from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.constants import JoinRequestStatus
from app.domain.entities.join_request import JoinRequest


def join_request_to_document(request: JoinRequest) -> dict[str, Any]:
    return {
        "_id": str(request.id),
        "room_id": str(request.room_id),
        "user_id": str(request.user_id),
        "status": request.status.value,
        "handled_by": str(request.handled_by) if request.handled_by else None,
        "message": request.message,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    }


def document_to_join_request(doc: dict[str, Any]) -> JoinRequest:
    return JoinRequest(
        id=UUID(doc["_id"]),
        room_id=UUID(doc["room_id"]),
        user_id=UUID(doc["user_id"]),
        status=JoinRequestStatus(doc["status"]),
        handled_by=UUID(doc["handled_by"]) if doc.get("handled_by") else None,
        message=doc.get("message"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )

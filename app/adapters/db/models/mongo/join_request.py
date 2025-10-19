from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.join_request import JoinRequest


def join_request_to_document(request: JoinRequest) -> dict[str, Any]:
    return {
        "_id": str(request.id),
        "room_id": str(request.room_id),
        "user_id": str(request.user_id),
        "message": request.message,
        "created_at": request.created_at,
    }


def document_to_join_request(doc: dict[str, Any]) -> JoinRequest:
    return JoinRequest(
        id=UUID(doc["_id"]),
        room_id=UUID(doc["room_id"]),
        user_id=UUID(doc["user_id"]),
        message=doc.get("message"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
    )

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.chat_room import ChatRoom


def chat_room_to_document(room: ChatRoom) -> dict[str, Any]:
    return {
        "_id": str(room.id),
        "name": room.name,
        "participants": [str(uid) for uid in room.participants],
        "created_at": room.created_at,
        "updated_at": room.updated_at,
    }


def document_to_chat_room(doc: dict[str, Any]) -> ChatRoom:
    return ChatRoom(
        id=UUID(doc["_id"]),
        name=doc["name"],
        participants=[UUID(uid) for uid in doc.get("participants", [])],
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )

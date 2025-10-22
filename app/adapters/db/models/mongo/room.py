from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.domain.entities.room import Room


def room_to_document(room: Room) -> dict[str, Any]:
    return {
        "_id": str(room.id),
        "name": room.name,
        "is_public": room.is_public,
        "created_by": str(room.created_by),
        "participants_count": room.participants_count,
        "description": room.description,
        "created_at": room.created_at,
        "updated_at": room.updated_at,
    }


def document_to_room(doc: dict[str, Any]) -> Room:
    return Room(
        id=UUID(doc["_id"]),
        name=doc["name"],
        is_public=doc["is_public"],
        created_by=UUID(doc["created_by"]),
        participants_count=doc["participants_count"],
        description=doc["description"],
        created_at=doc.get("created_at", datetime.now(UTC)),
        updated_at=doc.get("updated_at", datetime.now(UTC)),
    )

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.constants import RoomRole
from app.domain.entities.room_membership import RoomMembership


def room_membership_to_document(room_membership: RoomMembership) -> dict[str, Any]:
    return {
        "room_id": str(room_membership.room_id),
        "user_id": str(room_membership.user_id),
        "role": room_membership.role.value,
        "joined_at": room_membership.joined_at,
    }


def document_to_room_membership(doc: dict[str, Any]) -> RoomMembership:
    return RoomMembership(
        room_id=UUID(doc["room_id"]),
        user_id=UUID(doc["user_id"]),
        role=RoomRole(doc["role"]),
        joined_at=doc.get("joined_at", datetime.now(UTC)),
    )

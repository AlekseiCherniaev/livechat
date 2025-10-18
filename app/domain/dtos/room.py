from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.room import Room


@dataclass
class RoomCreateDTO:
    name: str
    description: str | None
    is_public: bool
    created_by: UUID


@dataclass
class RoomUpdateDTO:
    created_by: UUID
    description: str | None = None
    is_public: bool | None = None


@dataclass
class RoomPublicDTO:
    name: str
    description: str | None
    is_public: bool
    created_by: UUID
    participants_count: int
    created_at: datetime
    updated_at: datetime
    id: UUID


def room_to_dto(room: Room) -> RoomPublicDTO:
    return RoomPublicDTO(
        name=room.name,
        description=room.description,
        is_public=room.is_public,
        created_by=room.created_by,
        participants_count=room.participants_count,
        created_at=room.created_at,
        updated_at=room.updated_at,
        id=room.id,
    )

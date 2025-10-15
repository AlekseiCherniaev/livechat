from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class RoomCreateDTO:
    name: str
    description: str | None
    is_public: bool
    created_by: UUID


@dataclass
class RoomUpdateDTO:
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

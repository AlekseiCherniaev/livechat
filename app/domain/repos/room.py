from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.room import Room


class RoomRepository(Protocol):
    async def save(self, room: Room, db_session: Any | None = None) -> Room: ...

    async def get_by_id(
        self, room_id: UUID, db_session: Any | None = None
    ) -> Room | None: ...

    async def search(
        self, query: str, limit: int, db_session: Any | None = None
    ) -> list[Room]: ...

    async def delete_by_id(
        self, room_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def list_top_room(
        self, limit: int, only_public: bool, db_session: Any | None = None
    ) -> list[Room]: ...

    async def add_participant(
        self, room_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def remove_participant(
        self, room_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def exists(self, name: str, db_session: Any | None = None) -> bool: ...

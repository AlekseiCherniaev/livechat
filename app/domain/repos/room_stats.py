from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.room import Room
from app.domain.entities.room_stats import RoomStats


class RoomStatsRepository(Protocol):
    async def save(self, stats: RoomStats, db_session: Any | None = None) -> None: ...

    async def get(
        self, room_id: UUID, db_session: Any | None = None
    ) -> RoomStats | None: ...

    async def update(self, stats: RoomStats, db_session: Any | None = None) -> None: ...

    async def top_rooms_by_messages(
        self, limit: int, db_session: Any | None = None
    ) -> list[Room]: ...

    async def top_rooms_by_users(
        self, limit: int, db_session: Any | None = None
    ) -> list[Room]: ...

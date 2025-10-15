from typing import Protocol
from uuid import UUID

from app.domain.entities.room import Room
from app.domain.entities.room_stats import RoomStats


class RoomStatsRepository(Protocol):
    async def save(self, stats: RoomStats) -> None: ...

    async def get(self, room_id: UUID) -> RoomStats | None: ...

    async def update(self, stats: RoomStats) -> None: ...

    async def top_rooms_by_messages(self, limit: int = 10) -> list[Room]: ...

    async def top_rooms_by_users(self, limit: int = 10) -> list[Room]: ...

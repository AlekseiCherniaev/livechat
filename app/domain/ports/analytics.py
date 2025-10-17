from typing import Protocol
from uuid import UUID

from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.room_stats import RoomStats


class AnalyticsPort(Protocol):
    async def publish_event(self, event: AnalyticsEvent) -> None: ...

    async def get_room_stats(self, room_id: UUID) -> RoomStats | None: ...

    async def get_user_activity(self, user_id: UUID) -> dict[str, int] | None: ...

    async def top_active_rooms(self, limit: int) -> list[RoomStats]: ...

    async def messages_per_minute(self, room_id: UUID, since_minutes: int) -> int: ...

from typing import Protocol
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.room_stats import RoomStats


class AnalyticsPort(Protocol):
    async def publish_event(self, event: AnalyticsEvent) -> None:
        """Save an analytics event, e.g. user joined room, message sent, etc."""
        pass

    async def get_room_stats(self, room_id: str) -> RoomStats | None:
        pass

    async def update_room_stats(self, stats: RoomStats) -> None:
        pass

    async def get_user_activity(self, user_id: str) -> dict[str, int] | None:
        """For example {'messages': 42, 'rooms_joined': 3}"""
        pass

    async def top_active_rooms(self, limit: int = 10) -> list[RoomStats]:
        pass

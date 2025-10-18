from uuid import UUID

from app.domain.entities.room_stats import RoomStats
from app.domain.exceptions.analytics import RoomStatsNotFound, UserActivityNotFound
from app.domain.ports.analytics import AnalyticsPort


class AnalyticsService:
    def __init__(
        self,
        analytics_port: AnalyticsPort,
    ):
        self._analytics = analytics_port

    async def get_room_stats(self, room_id: UUID) -> RoomStats:
        rooms_stats = await self._analytics.get_room_stats(room_id=room_id)
        if not rooms_stats:
            raise RoomStatsNotFound

        return rooms_stats

    async def get_user_activity(self, user_id: UUID) -> dict[str, int]:
        user_activity = await self._analytics.get_user_activity(user_id=user_id)
        if not user_activity:
            raise UserActivityNotFound

        return user_activity

    async def top_active_rooms(self, limit: int) -> list[RoomStats]:
        return await self._analytics.top_active_rooms(limit=limit)

    async def messages_per_minute(self, room_id: UUID, since_minutes: int) -> int:
        return await self._analytics.messages_per_minute(
            room_id=room_id, since_minutes=since_minutes
        )

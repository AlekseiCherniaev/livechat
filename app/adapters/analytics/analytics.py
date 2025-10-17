from datetime import datetime, timedelta
from uuid import UUID

import orjson
from cassandra.query import timezone
from clickhouse_connect.driver.asyncclient import AsyncClient

from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.room_stats import RoomStats


class ClickHouseAnalyticsRepository:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def publish_event(self, event: AnalyticsEvent) -> None:
        payload_serialized = None
        if event.payload is not None:
            payload_serialized = orjson.dumps(event.payload).decode("utf-8")

        await self._client.insert(
            "analytics_events",
            [
                [
                    str(event.id),
                    event.event_type.value,
                    str(event.user_id) if event.user_id else None,
                    str(event.room_id) if event.room_id else None,
                    event.created_at,
                    payload_serialized,
                ]
            ],
            column_names=[
                "id",
                "event_type",
                "user_id",
                "room_id",
                "created_at",
                "payload",
            ],
        )

    async def get_room_stats(self, room_id: UUID) -> RoomStats | None:
        query = f"""
        SELECT
            COUNT(*) AS total_messages,
            COUNT(DISTINCT user_id) AS active_users,
            MAX(created_at) AS last_updated
        FROM analytics_events
        WHERE room_id = '{room_id}'
        """

        result = await self._client.query(query)
        if not result.result_rows:
            return None

        row = next(result.named_results())
        return RoomStats(
            room_id=room_id,
            total_messages=row["total_messages"],
            active_users=row["active_users"],
            last_updated=row["last_updated"],
        )

    async def get_user_activity(self, user_id: UUID) -> dict[str, int] | None:
        query = f"""
                SELECT
                    COUNT(*) AS messages,
                    COUNT(DISTINCT room_id) AS rooms_joined
                FROM analytics_events
                WHERE user_id = '{user_id}'
                """

        result = await self._client.query(query)
        if not result.result_rows:
            return None

        row = next(result.named_results())
        return {"messages": row["messages"], "rooms_joined": row["rooms_joined"]}

    async def top_active_rooms(self, limit: int) -> list[RoomStats]:
        query = f"""
                SELECT
                    room_id,
                    COUNT(*) AS total_messages,
                    COUNT(DISTINCT user_id) AS active_users,
                    MAX(created_at) AS last_updated
                FROM analytics_events
                GROUP BY room_id
                ORDER BY total_messages DESC
                LIMIT {limit}
                """

        result = await self._client.query(query)
        rows = list(result.named_results())
        return [
            RoomStats(
                room_id=row["room_id"],
                total_messages=row["total_messages"],
                active_users=row["active_users"],
                last_updated=row["last_updated"],
            )
            for row in rows
        ]

    async def messages_per_minute(self, room_id: UUID, since_minutes: int) -> int:
        since_time = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        query = f"""
        SELECT COUNT(*) AS cnt
        FROM analytics_events
        WHERE room_id = '{room_id}' AND created_at >= toDateTime('{since_time.isoformat()}')
        """

        result = await self._client.query(query)
        if not result.result_rows:
            return 0
        row = next(result.named_results())
        return row["cnt"]

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import orjson
from cassandra.query import timezone
from clickhouse_connect.driver.asyncclient import AsyncClient

from app.core.constants import AnalyticsEventType
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.room_stats import RoomStats


class ClickHouseAnalyticsRepository:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def publish_event(self, event: AnalyticsEvent) -> None:
        payload_serialized = None
        if event.payload:
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
                    payload_serialized if payload_serialized else "",
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
                    COUNT(DISTINCT user_id) AS users_amount,
                    MAX(created_at) AS last_updated
                FROM analytics_events
                WHERE room_id = '{room_id}'
                  AND event_type = '{AnalyticsEventType.MESSAGE_SENT.value}'
                """

        result = await self._client.query(query)
        if not result.result_rows:
            return None

        row = next(result.named_results())
        return RoomStats(
            room_id=room_id,
            total_messages=row["total_messages"],
            users_amount=row["users_amount"],
            last_updated=row["last_updated"],
        )

    async def get_user_activity(self, user_id: UUID) -> dict[str, int] | None:
        query_messages = f"""
                SELECT COUNT(*) AS messages
                FROM analytics_events
                WHERE user_id = '{user_id}'
                  AND event_type = '{AnalyticsEventType.MESSAGE_SENT.value}'
                """

        query_rooms = f"""
                SELECT COUNT(DISTINCT room_id) AS rooms_joined
                FROM analytics_events
                WHERE user_id = '{user_id}'
                  AND event_type = '{AnalyticsEventType.USER_JOINED_ROOM.value}'
                """

        messages_res = await self._client.query(query_messages)
        rooms_res = await self._client.query(query_rooms)

        if not messages_res.result_rows and not rooms_res.result_rows:
            return None

        messages = (
            next(messages_res.named_results())["messages"]
            if messages_res.result_rows
            else 0
        )
        rooms_joined = (
            next(rooms_res.named_results())["rooms_joined"]
            if rooms_res.result_rows
            else 0
        )

        return {"messages": messages, "rooms_joined": rooms_joined}

    async def top_active_rooms(self, limit: int) -> list[RoomStats]:
        query = f"""
                SELECT
                    room_id,
                    COUNT(*) AS total_messages,
                    COUNT(DISTINCT user_id) AS users_amount,
                    MAX(created_at) AS last_updated
                FROM analytics_events
                WHERE event_type = '{AnalyticsEventType.MESSAGE_SENT.value}'
                GROUP BY room_id
                ORDER BY total_messages DESC
                LIMIT {limit}
                """

        result = await self._client.query(query)
        return [
            RoomStats(
                room_id=row["room_id"],
                total_messages=row["total_messages"],
                users_amount=row["users_amount"],
                last_updated=row["last_updated"],
            )
            for row in list(result.named_results())
        ]

    async def messages_per_minute(self, room_id: UUID, since_minutes: int) -> int:
        since_time = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        since_str = since_time.strftime("%Y-%m-%d %H:%M:%S")

        query = f"""
                SELECT COUNT(*) AS cnt
                FROM analytics_events
                WHERE room_id = '{room_id}'
                  AND event_type = '{AnalyticsEventType.MESSAGE_SENT.value}'
                  AND created_at >= toDateTime('{since_str}')
                """

        result = await self._client.query(query)
        if not result.result_rows:
            return 0

        row = next(result.named_results())
        return int(row["cnt"])

    async def get_user_retention(self, days: int) -> float:
        since_time = datetime.now(timezone.utc) - timedelta(days=days)
        since_str = since_time.strftime("%Y-%m-%d %H:%M:%S")

        query = f"""
        SELECT
            COUNT(DISTINCT user_id) AS active,
            (SELECT COUNT(DISTINCT user_id) FROM analytics_events
             WHERE event_type = '{AnalyticsEventType.USER_REGISTERED.value}') AS total
        FROM analytics_events
        WHERE event_type = '{AnalyticsEventType.USER_LOGGED_IN.value}'
          AND created_at >= toDateTime('{since_str}')
        """

        result = await self._client.query(query)
        row = next(result.named_results())
        return (row["active"] / row["total"]) * 100 if row["total"] else 0.0

    async def message_edit_delete_ratio(self) -> dict[str, float]:
        query = f"""
        SELECT
            COUNTIf(event_type = '{AnalyticsEventType.MESSAGE_SENT.value}') AS sent,
            COUNTIf(event_type = '{AnalyticsEventType.MESSAGE_EDITED.value}') AS edited,
            COUNTIf(event_type = '{AnalyticsEventType.MESSAGE_DELETED.value}') AS deleted
        FROM analytics_events
        """

        result = await self._client.query(query)
        row = next(result.named_results())
        sent = row["sent"] or 1
        return {
            "edit_ratio": row["edited"] / sent,
            "delete_ratio": row["deleted"] / sent,
        }

    async def top_social_users(self, limit: int = 10) -> list[dict[str, Any]]:
        query = f"""
        SELECT
            user_id,
            COUNT(DISTINCT room_id) AS rooms,
            COUNTIf(event_type = '{AnalyticsEventType.MESSAGE_SENT.value}') AS messages
        FROM analytics_events
        WHERE user_id IS NOT NULL
        GROUP BY user_id
        ORDER BY rooms DESC, messages DESC
        LIMIT {limit}
        """

        result = await self._client.query(query)
        return list(result.named_results())

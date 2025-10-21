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
        event_type = AnalyticsEventType.MESSAGE_SENT.value
        query = """
                SELECT
                    COUNT(*) AS total_messages,
                    uniqExact(user_id) AS users_amount,
                    MAX(created_at) AS last_updated
                FROM analytics_events
                WHERE room_id = %(room_id)s
                  AND event_type = %(event_type)s
                """

        result = await self._client.query(
            query, {"room_id": str(room_id), "event_type": event_type}
        )

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
        query = """
                SELECT
                    COUNTIf(event_type = %(message_sent)s) AS messages,
                    uniqExactIf(room_id, event_type = %(user_joined)s) AS rooms_joined
                FROM analytics_events
                WHERE user_id = %(user_id)s
                """

        result = await self._client.query(
            query,
            {
                "user_id": str(user_id),
                "message_sent": AnalyticsEventType.MESSAGE_SENT.value,
                "user_joined": AnalyticsEventType.USER_JOINED_ROOM.value,
            },
        )

        if not result.result_rows:
            return None

        row = next(result.named_results())
        return {
            "messages": row["messages"] or 0,
            "rooms_joined": row["rooms_joined"] or 0,
        }

    async def top_active_rooms(self, limit: int) -> list[RoomStats]:
        query = """
                SELECT
                    room_id,
                    COUNT(*) AS total_messages,
                    uniqExact(user_id) AS users_amount,
                    MAX(created_at) AS last_updated
                FROM analytics_events
                WHERE event_type = %(event_type)s
                GROUP BY room_id
                ORDER BY total_messages DESC
                LIMIT %(limit)s
                """

        result = await self._client.query(
            query, {"event_type": AnalyticsEventType.MESSAGE_SENT.value, "limit": limit}
        )

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

        query = """
                SELECT COUNT(*) AS cnt
                FROM analytics_events
                WHERE room_id = %(room_id)s
                  AND event_type = %(event_type)s
                  AND created_at >= toDateTime(%(since_time)s)
                """

        result = await self._client.query(
            query,
            parameters={
                "room_id": str(room_id),
                "event_type": AnalyticsEventType.MESSAGE_SENT.value,
                "since_time": since_str,
            },
        )

        if not result.result_rows:
            return 0

        row = next(result.named_results())
        return int(row["cnt"])

    async def get_user_retention(self, days: int) -> float:
        since_time = datetime.now(timezone.utc) - timedelta(days=days)
        since_str = since_time.strftime("%Y-%m-%d %H:%M:%S")

        query = """
                    SELECT
                        uniqExact(user_id) AS active,
                        (SELECT uniqExact(user_id) FROM analytics_events
                         WHERE event_type = %(registered_event)s) AS total
                    FROM analytics_events
                    WHERE event_type = %(login_event)s
                      AND created_at >= toDateTime(%(since_time)s)
                    """

        result = await self._client.query(
            query,
            parameters={
                "registered_event": AnalyticsEventType.USER_REGISTERED.value,
                "login_event": AnalyticsEventType.USER_LOGGED_IN.value,
                "since_time": since_str,
            },
        )

        row = next(result.named_results())
        return (row["active"] / row["total"]) * 100 if row["total"] else 0.0

    async def message_edit_delete_ratio(self) -> dict[str, float]:
        query = """
                    SELECT
                        COUNTIf(event_type = %(sent_event)s) AS sent,
                        COUNTIf(event_type = %(edited_event)s) AS edited,
                        COUNTIf(event_type = %(deleted_event)s) AS deleted
                    FROM analytics_events
                    """

        result = await self._client.query(
            query,
            parameters={
                "sent_event": AnalyticsEventType.MESSAGE_SENT.value,
                "edited_event": AnalyticsEventType.MESSAGE_EDITED.value,
                "deleted_event": AnalyticsEventType.MESSAGE_DELETED.value,
            },
        )

        row = next(result.named_results())
        sent = row["sent"] or 1
        return {
            "edit_ratio": row["edited"] / sent,
            "delete_ratio": row["deleted"] / sent,
        }

    async def top_social_users(self, limit: int = 10) -> list[dict[str, Any]]:
        query = """
                SELECT
                    user_id,
                    uniqExact(room_id) AS rooms,
                    COUNTIf(event_type = %(sent_event)s) AS messages
                FROM analytics_events
                WHERE user_id IS NOT NULL
                GROUP BY user_id
                ORDER BY rooms DESC, messages DESC
                LIMIT %(limit)s
                """

        result = await self._client.query(
            query,
            parameters={
                "sent_event": AnalyticsEventType.MESSAGE_SENT.value,
                "limit": limit,
            },
        )

        return list(result.named_results())

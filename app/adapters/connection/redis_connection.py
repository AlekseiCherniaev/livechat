from uuid import UUID

import orjson
from redis.asyncio import Redis

from app.core.constants import BroadcastEventType
from app.core.settings import get_settings
from app.domain.entities.event_payload import EventPayload


class RedisConnectionPort:
    def __init__(
        self, redis: Redis, ttl: int = get_settings().web_socket_session_ttl_seconds
    ):
        self._redis = redis
        self._ttl = ttl

    async def connect_user_to_room(self, user_id: UUID, room_id: UUID) -> None:
        user_connections_key = f"ws:user:{user_id}:connections"
        room_users_key = f"ws:room:{room_id}:users"

        await self._redis.sadd(user_connections_key, str(room_id))  # type: ignore[misc]
        await self._redis.sadd(room_users_key, str(user_id))  # type: ignore[misc]
        await self._redis.expire(user_connections_key, self._ttl)
        await self._redis.expire(room_users_key, self._ttl)

    async def disconnect_user(self, user_id: UUID) -> None:
        user_connections_key = f"ws:user:{user_id}:connections"
        room_ids = await self._redis.smembers(user_connections_key)  # type: ignore[misc]

        for room_id in room_ids:
            room_users_key = f"ws:room:{room_id}:users"
            await self._redis.srem(room_users_key, str(user_id))  # type: ignore[misc]

        await self._redis.delete(user_connections_key)

    async def disconnect_user_from_room(self, user_id: UUID, room_id: UUID) -> None:
        user_connections_key = f"ws:user:{user_id}:connections"
        room_users_key = f"ws:room:{room_id}:users"

        await self._redis.srem(user_connections_key, str(room_id))  # type: ignore[misc]
        await self._redis.srem(room_users_key, str(user_id))  # type: ignore[misc]

    async def get_user_connections(self, user_id: UUID) -> set[UUID]:
        key = f"ws:user:{user_id}:connections"
        room_ids = await self._redis.smembers(key)  # type: ignore[misc]
        return {UUID(rid) for rid in room_ids}

    async def broadcast_event(
        self, room_id: UUID, event_type: BroadcastEventType, event_payload: EventPayload
    ) -> None:
        channel = f"ws:room:{room_id}"
        message = {
            "event_type": event_type.value,
            "payload": {
                "user_id": str(event_payload.user_id),
                "username": event_payload.username,
                "payload": event_payload.payload,
            },
        }
        await self._redis.publish(channel, orjson.dumps(message))

    async def send_event_to_user(
        self, user_id: UUID, event_type: BroadcastEventType, event_payload: EventPayload
    ) -> None:
        channel = f"ws:user:{user_id}"
        message = {
            "event_type": event_type.value,
            "payload": event_payload.payload,
        }
        await self._redis.publish(channel, orjson.dumps(message))

    async def list_active_user_ids_in_room(self, room_id: UUID) -> list[UUID]:
        room_key = f"ws:room:{room_id}:users"
        user_ids = await self._redis.smembers(room_key)  # type: ignore[misc]
        return [UUID(uid) for uid in user_ids]

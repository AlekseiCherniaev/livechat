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
        room_key = f"ws:room:{room_id}:users"
        user_rooms_key = f"ws:user:{user_id}:rooms"
        await self._redis.sadd(room_key, str(user_id))  # type: ignore[misc]
        await self._redis.sadd(user_rooms_key, str(room_id))  # type: ignore[misc]
        await self._redis.expire(room_key, self._ttl)
        await self._redis.expire(user_rooms_key, self._ttl)

    async def disconnect_user_from_room(self, user_id: UUID, room_id: UUID) -> None:
        room_key = f"ws:room:{room_id}:users"
        user_rooms_key = f"ws:user:{user_id}:rooms"
        await self._redis.srem(room_key, str(user_id))  # type: ignore[misc]
        await self._redis.srem(user_rooms_key, str(room_id))  # type: ignore[misc]

        if await self._redis.scard(room_key) > 0:  # type: ignore[misc]
            await self._redis.expire(room_key, self._ttl)
        if await self._redis.scard(user_rooms_key) > 0:  # type: ignore[misc]
            await self._redis.expire(user_rooms_key, self._ttl)

    async def broadcast_event(
        self, room_id: UUID, event_type: BroadcastEventType, event_payload: EventPayload
    ) -> None:
        channel = f"ws:room:{room_id}"
        message = {
            "event_type": event_type.value,
            "payload": {
                "username": event_payload.username,
                "content": event_payload.content,
                "is_typing": event_payload.is_typing,
            },
        }
        await self._redis.publish(channel, orjson.dumps(message))

    async def send_event_to_user(
        self, user_id: UUID, event_type: BroadcastEventType, event_payload: EventPayload
    ) -> None:
        channel = f"ws:user:{user_id}:notifications"
        message = {
            "event_type": event_type.value,
            "payload": event_payload.payload,
        }
        await self._redis.publish(channel, orjson.dumps(message))

    async def list_active_user_ids_in_room(self, room_id: UUID) -> list[UUID]:
        room_key = f"ws:room:{room_id}:users"
        user_ids = await self._redis.smembers(room_key)  # type: ignore[misc]
        return [UUID(uid) for uid in user_ids]

    async def is_user_online(self, user_id: UUID) -> bool:
        user_rooms_key = f"ws:user:{user_id}:rooms"
        return await self._redis.scard(user_rooms_key) > 0  # type: ignore

from datetime import timezone, datetime
from uuid import UUID

import orjson
from redis.asyncio import Redis

from app.core.constants import BroadcastEventType
from app.domain.entities.event_payload import EventPayload
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.ports.connection import ConnectionPort


class RedisConnectionPort(ConnectionPort):
    def __init__(self, redis: Redis):
        self._redis = redis

    async def connect(self, session: WebSocketSession) -> None:
        session_key = f"ws:session:{session.session_id}"
        room_key = f"ws:room:{session.room_id}:users"
        user_rooms_key = f"ws:user:{session.user_id}:rooms"

        session_data = orjson.dumps(session.__dict__)
        await self._redis.set(session_key, session_data)
        await self._redis.sadd(room_key, str(session.user_id))
        await self._redis.sadd(user_rooms_key, str(session.room_id))

    async def disconnect(self, session_id: UUID) -> None:
        session_key = f"ws:session:{session_id}"
        session_data = await self._redis.get(session_key)
        if not session_data:
            return

        session = WebSocketSession(**orjson.loads(session_data))
        await self._redis.delete(session_key)
        await self._redis.srem(f"ws:room:{session.room_id}:users", str(session.user_id))
        await self._redis.srem(f"ws:user:{session.user_id}:rooms", str(session.room_id))

    async def broadcast_event(
        self, room_id: UUID, event_type: BroadcastEventType, payload: EventPayload
    ) -> None:
        channel = f"ws:room:{room_id}"
        message = {
            "event_type": event_type.value,
            "payload": payload.__dict__,
        }
        await self._redis.publish(channel, orjson.dumps(message))

    async def disconnect_user_from_room(self, user_id: UUID, room_id: UUID) -> None:
        room_key = f"ws:room:{room_id}:users"
        user_rooms_key = f"ws:user:{user_id}:rooms"
        await self._redis.srem(room_key, str(user_id))
        await self._redis.srem(user_rooms_key, str(room_id))

    async def list_active_user_ids_in_room(self, room_id: UUID) -> list[UUID]:
        room_key = f"ws:room:{room_id}:users"
        user_ids = await self._redis.smembers(room_key)
        return [UUID(uid) for uid in user_ids]

    async def update_ping(self, session_id: UUID) -> None:
        session_key = f"ws:session:{session_id}"
        data = await self._redis.get(session_key)
        if not data:
            return
        session = WebSocketSession(**orjson.loads(data))
        session.last_ping_at = datetime.now(timezone.utc)
        await self._redis.set(session_key, orjson.dumps(session.__dict__))

    async def is_user_online(self, user_id: UUID) -> bool:
        user_rooms_key = f"ws:user:{user_id}:rooms"
        rooms = await self._redis.scard(user_rooms_key)
        return rooms > 0

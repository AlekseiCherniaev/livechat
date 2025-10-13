import asyncio
import orjson
from uuid import UUID
from redis.asyncio import Redis

from app.adapters.db.models.redis_websocker_session import (
    session_to_dict,
    dict_to_session,
)
from app.domain.entities.websocket_session import WebSocketSession
from app.core.settings import get_settings


class RedisWebSocketSessionRepository:
    def __init__(
        self, redis: Redis, ttl: int = get_settings().web_socket_session_ttl_seconds
    ):
        self._redis = redis
        self._ttl = ttl

    @staticmethod
    def _session_key(session_id: UUID) -> str:
        return f"ws_session:{session_id}"

    @staticmethod
    def _user_sessions_key(user_id: UUID) -> str:
        return f"user_ws_sessions:{user_id}"

    async def save(self, session: WebSocketSession) -> None:
        data = session_to_dict(session)
        await self._redis.set(
            name=self._session_key(session.id),
            value=orjson.dumps(data),
            ex=self._ttl,
        )
        await self._redis.sadd(  # type: ignore[misc]
            self._user_sessions_key(session.user_id), str(session.id)
        )
        await self._redis.expire(self._user_sessions_key(session.user_id), self._ttl)

    async def get(self, session_id: UUID) -> WebSocketSession | None:
        raw = await self._redis.get(self._session_key(session_id))
        if not raw:
            return None
        return dict_to_session(orjson.loads(raw))

    async def list_by_user_id(self, user_id: UUID) -> list[WebSocketSession]:
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        sessions = await asyncio.gather(*(self.get(UUID(sid)) for sid in session_ids))
        return [s for s in sessions if s]

    async def delete_by_id(self, session_id: UUID) -> None:
        session = await self.get(session_id)
        if session:
            await self._redis.srem(  # type: ignore[misc]
                self._user_sessions_key(session.user_id), str(session_id)
            )
        await self._redis.delete(self._session_key(session_id))

    async def delete_by_user_id(self, user_id: UUID) -> None:
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        if session_ids:
            await self._redis.delete(*(self._session_key(UUID(s)) for s in session_ids))
        await self._redis.delete(self._user_sessions_key(user_id))

    async def is_online(self, user_id: UUID) -> bool:
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        for sid in session_ids:
            s = await self.get(UUID(sid))
            if s and s.disconnected_at is None:
                return True
        return False

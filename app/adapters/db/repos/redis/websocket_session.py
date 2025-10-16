import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import orjson
from redis.asyncio import Redis

from app.adapters.db.models.redis.websocker_session import (
    session_to_dict,
    dict_to_session,
)
from app.core.settings import get_settings
from app.domain.entities.websocket_session import WebSocketSession


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

    async def save(
        self, session: WebSocketSession, db_session: Any | None = None
    ) -> None:
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

    async def get_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> WebSocketSession | None:
        raw = await self._redis.get(self._session_key(session_id))
        if not raw:
            return None

        return dict_to_session(orjson.loads(raw))

    async def list_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> list[WebSocketSession]:
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        sessions = await asyncio.gather(
            *(self.get_by_id(UUID(sid)) for sid in session_ids)
        )
        return [s for s in sessions if s]

    async def delete_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> None:
        session = await self.get_by_id(session_id)
        if session:
            await self._redis.srem(  # type: ignore[misc]
                self._user_sessions_key(session.user_id), str(session_id)
            )
        await self._redis.delete(self._session_key(session_id))

    async def delete_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None:
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        if session_ids:
            await self._redis.delete(*(self._session_key(UUID(s)) for s in session_ids))
        await self._redis.delete(self._user_sessions_key(user_id))

    async def count_by_room(self, room_id: UUID, db_session: Any | None = None) -> int:
        pattern = "ws_session:*"
        count = 0
        async for key in self._redis.scan_iter(match=pattern):
            raw = await self._redis.get(key)
            if not raw:
                continue
            session = dict_to_session(orjson.loads(raw))
            if session.room_id == room_id:
                count += 1
        return count

    async def update_last_ping(
        self, session_id: UUID, db_session: Any | None = None
    ) -> None:
        raw = await self._redis.get(self._session_key(session_id))
        if not raw:
            return

        data = orjson.loads(raw)
        data["last_ping_at"] = datetime.now(timezone.utc).isoformat()
        await self._redis.set(
            name=self._session_key(session_id),
            value=orjson.dumps(data),
            ex=self._ttl,
        )

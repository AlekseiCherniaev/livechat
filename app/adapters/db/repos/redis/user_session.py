from typing import Any
from uuid import UUID

import orjson
from redis.asyncio import Redis

from app.adapters.db.models.redis.user_session import dict_to_session, session_to_dict
from app.core.settings import get_settings
from app.domain.entities.user_session import UserSession


class RedisSessionRepository:
    def __init__(
        self, redis: Redis, ttl: int = get_settings().user_session_ttl_seconds
    ):
        self._redis: Redis = redis
        self._ttl = ttl
        self._sliding_threshold = 600

    @staticmethod
    def _session_key(session_id: UUID) -> str:
        return f"session:{session_id}"

    @staticmethod
    def _user_sessions_key(user_id: UUID) -> str:
        return f"user_sessions:{user_id}"

    async def save(self, session: UserSession, db_session: Any | None = None) -> None:
        data = session_to_dict(session=session)
        await self._redis.set(
            name=self._session_key(data["id"]), value=orjson.dumps(data), ex=self._ttl
        )
        await self._redis.sadd(  # type: ignore[misc]
            self._user_sessions_key(session.user_id), str(session.id)
        )
        await self._redis.expire(self._user_sessions_key(session.user_id), self._ttl)

    async def get_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> UserSession | None:
        raw = await self._redis.get(name=self._session_key(session_id))
        if not raw:
            return None

        session = dict_to_session(orjson.loads(raw))
        ttl = await self._redis.ttl(self._session_key(session_id))
        if ttl is not None and ttl < self._sliding_threshold:
            await self._redis.expire(self._session_key(session_id), self._ttl)
            await self._redis.expire(
                self._user_sessions_key(session.user_id), self._ttl
            )

        return session

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

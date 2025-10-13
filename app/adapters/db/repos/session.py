import asyncio
from uuid import UUID

import orjson
from redis.asyncio import Redis
from app.adapters.db.models.redis_session import dict_to_session, session_to_dict
from app.core.settings import get_settings
from app.domain.entities.user_session import UserSession


class RedisSessionRepository:
    def __init__(self, redis: Redis, ttl: int = get_settings().session_ttl_seconds):
        self._redis: Redis = redis
        self._ttl = ttl

    @staticmethod
    def _session_key(session_id: UUID) -> str:
        return f"session:{session_id}"

    @staticmethod
    def _user_sessions_key(user_id: UUID) -> str:
        return f"user_sessions:{user_id}"

    async def save(self, session: UserSession) -> None:
        data = session_to_dict(session=session)
        await self._redis.set(
            name=self._session_key(data["id"]), value=orjson.dumps(data), ex=self._ttl
        )
        await self._redis.sadd(  # type: ignore[misc]
            self._user_sessions_key(session.user_id), str(session.id)
        )
        await self._redis.expire(self._user_sessions_key(session.user_id), self._ttl)

    async def get(self, session_id: UUID) -> UserSession | None:
        raw = await self._redis.get(name=self._session_key(session_id))
        if not raw:
            return None
        data = orjson.loads(raw)
        return dict_to_session(dict_session=data)

    async def list_by_user_id(self, user_id: UUID) -> list[UserSession]:
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        sessions = await asyncio.gather(*(self.get(UUID(sid)) for sid in session_ids))
        return [session for session in sessions if session]

    async def update(self, session: UserSession) -> None:
        # just re-save, overwriting old TTL
        await self.save(session)

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
        """User is considered online if at least one active session exists."""
        session_ids = await self._redis.smembers(self._user_sessions_key(user_id))  # type: ignore[misc]
        for sid in session_ids:
            sess = await self.get(UUID(sid))
            if sess and not sess.disconnected_at:
                return True
        return False

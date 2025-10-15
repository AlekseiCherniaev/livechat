from typing import Protocol
from uuid import UUID

from app.domain.entities.user_session import UserSession


class UserSessionRepository(Protocol):
    async def save(self, session: UserSession) -> None: ...

    async def get(self, session_id: UUID) -> UserSession | None: ...

    async def delete_by_id(self, session_id: UUID) -> None: ...

    async def delete_by_user_id(self, user_id: UUID) -> None: ...

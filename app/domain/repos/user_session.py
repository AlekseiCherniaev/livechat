from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.user_session import UserSession


class UserSessionRepository(Protocol):
    async def save(
        self, session: UserSession, db_session: Any | None = None
    ) -> None: ...

    async def get_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> UserSession | None: ...

    async def delete_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def delete_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

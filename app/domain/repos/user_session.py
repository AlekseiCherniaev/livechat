from typing import Protocol
from uuid import UUID

from app.domain.entities.user_session import UserSession


class UserSessionRepository(Protocol):
    async def save(self, session: UserSession) -> None:
        pass

    async def get(self, session_id: UUID) -> UserSession | None:
        pass

    async def list_by_user_id(self, user_id: UUID) -> list[UserSession]:
        pass

    async def update(self, session: UserSession) -> None:
        pass

    async def delete_by_id(self, session_id: UUID) -> None:
        pass

    async def delete_by_user_id(self, user_id: UUID) -> None:
        pass

from typing import Protocol
from app.domain.entities.user_session import UserSession


class SessionRepository(Protocol):
    async def save(self, session: UserSession) -> None:
        pass

    async def get(self, session_id: str) -> UserSession | None:
        pass

    async def update(self, session: UserSession) -> None:
        pass

    async def delete_by_id(self, session_id: str) -> None:
        pass

    async def is_online(self, user_id: str) -> bool:
        pass

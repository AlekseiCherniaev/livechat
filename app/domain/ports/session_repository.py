from typing import Protocol
from app.domain.entities.user_session import UserSession


class SessionRepositoryPort(Protocol):
    async def save(self, session: UserSession) -> None:
        pass

    async def get(self, session_id: str) -> UserSession | None:
        pass

    async def update(self, session: UserSession) -> None:
        pass

    async def delete_by_id(self, session_id: str) -> None:
        pass

    async def set_online(self, user_id: str, room_id: str) -> None:
        pass

    async def set_offline(self, user_id: str, room_id: str) -> None:
        pass

    async def get_online_users(self, room_id: str) -> list[str]:
        pass

    async def is_online(self, user_id: str) -> bool:
        pass

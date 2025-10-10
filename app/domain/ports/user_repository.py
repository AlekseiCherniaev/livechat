from typing import Protocol
from app.domain.entities.user import User


class UserRepositoryPort(Protocol):
    async def get_by_id(self, user_id: str) -> User | None:
        pass

    async def get_by_username(self, username: str) -> User | None:
        pass

    async def save(self, user: User) -> User:
        pass

    async def update_last_active(self, user_id: str) -> None:
        pass

    async def delete_by_id(self, user_id: str) -> None:
        pass

    async def exists(self, username: str) -> bool:
        pass

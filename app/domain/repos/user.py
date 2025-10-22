from collections.abc import Collection
from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(Protocol):
    async def save(self, user: User, db_session: Any | None = None) -> User: ...

    async def get_by_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> User | None: ...

    async def get_by_username(
        self, username: str, db_session: Any | None = None
    ) -> User | None: ...

    async def get_by_ids(
        self, user_ids: Collection[UUID], db_session: Any | None = None
    ) -> list[User]: ...

    async def update_last_active(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def delete_by_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def exists(self, username: str, db_session: Any | None = None) -> bool: ...

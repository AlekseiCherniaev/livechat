from datetime import datetime
from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.message import Message


class MessageRepository(Protocol):
    async def save(self, message: Message, db_session: Any | None = None) -> None: ...

    async def get_recent_by_room(
        self, room_id: UUID, limit: int, db_session: Any | None = None
    ) -> list[Message]: ...

    async def get_by_id(
        self, message_id: UUID, db_session: Any | None = None
    ) -> Message | None: ...

    async def get_since(
        self, room_id: UUID, since: datetime, db_session: Any | None = None
    ) -> list[Message]: ...

    async def delete_by_id(
        self, message_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def count_by_room(
        self, room_id: UUID, db_session: Any | None = None
    ) -> int: ...

    async def list_by_user(
        self, user_id: UUID, limit: int, db_session: Any | None = None
    ) -> list[Message]: ...

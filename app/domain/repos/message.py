from datetime import datetime
from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.message import Message


class MessageRepository(Protocol):
    async def save(self, message: Message, db_session: Any | None = None) -> None: ...

    async def get_recent_by_room(
        self,
        room_id: UUID,
        limit: int,
        before: datetime | None,
        db_session: Any | None = None,
    ) -> list[Message]: ...

    async def get_since_all_rooms(
        self,
        since: datetime,
        limit: int,
        start_after: tuple[datetime, UUID] | None = None,
        db_session: Any | None = None,
    ) -> list[Message]: ...

    async def get_by_id(
        self, message_id: UUID, db_session: Any | None = None
    ) -> Message | None: ...

    async def delete_by_id(
        self, message_id: UUID, db_session: Any | None = None
    ) -> None: ...

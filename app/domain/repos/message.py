from typing import Protocol
from uuid import UUID

from app.domain.entities.message import Message


class MessageRepository(Protocol):
    async def save(self, message: Message) -> None:
        pass

    async def get_recent_by_room(self, room_id: UUID, limit: int) -> list[Message]:
        pass

    async def get_by_id(self, message_id: UUID) -> Message | None:
        pass

    async def delete_by_id(self, message_id: UUID) -> None:
        pass

    async def count_by_room(self, room_id: UUID) -> int:
        pass

    async def update_content(self, message_id: UUID, new_content: str) -> None:
        pass

    async def list_by_user(self, user_id: UUID, limit: int = 50) -> list[Message]:
        pass

from typing import Protocol
from app.domain.entities.message import Message


class MessageRepository(Protocol):
    async def save(self, message: Message) -> None:
        pass

    async def get_recent_by_room(self, room_id: str, limit: int) -> list[Message]:
        pass

    async def get_by_id(self, message_id: str) -> Message | None:
        pass

    async def delete_by_id(self, message_id: str) -> None:
        pass

    async def count_by_room(self, room_id: str) -> int:
        pass

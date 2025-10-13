from typing import Protocol
from uuid import UUID

from app.domain.entities.chat_room import ChatRoom


class ChatRoomRepository(Protocol):
    async def save(self, room: ChatRoom) -> ChatRoom:
        pass

    async def get(self, room_id: UUID) -> ChatRoom | None:
        pass

    async def update(self, room: ChatRoom) -> None:
        pass

    async def delete_by_id(self, room_id: UUID) -> None:
        pass

    async def list_all(self) -> list[ChatRoom]:
        pass

    async def list_by_user(self, user_id: UUID) -> list[ChatRoom]:
        pass

    async def add_participant(self, room_id: UUID, user_id: UUID) -> None:
        pass

    async def remove_participant(self, room_id: UUID, user_id: UUID) -> None:
        pass

    async def exists(self, name: str) -> bool:
        pass

    async def count_participants(self, room_id: UUID) -> int:
        pass

    async def find_most_active_rooms(self, limit: int = 10) -> list[ChatRoom]:
        pass

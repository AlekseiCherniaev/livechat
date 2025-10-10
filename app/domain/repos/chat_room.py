from typing import Protocol
from app.domain.entities.chat_room import ChatRoom


class ChatRoomRepository(Protocol):
    async def save(self, room: ChatRoom) -> ChatRoom:
        pass

    async def get(self, room_id: str) -> ChatRoom | None:
        pass

    async def update(self, room: ChatRoom) -> None:
        pass

    async def delete_by_id(self, room_id: str) -> None:
        pass

    async def list_all(self) -> list[ChatRoom]:
        pass

    async def list_by_user(self, user_id: str) -> list[ChatRoom]:
        pass

    async def add_participant(self, room_id: str, user_id: str) -> None:
        pass

    async def remove_participant(self, room_id: str, user_id: str) -> None:
        pass

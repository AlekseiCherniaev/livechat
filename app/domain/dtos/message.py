from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.message import Message


@dataclass
class MessagePublicDTO:
    room_id: UUID
    user_id: UUID
    content: str
    edited: bool
    id: UUID


def message_to_dto(message: Message) -> MessagePublicDTO:
    return MessagePublicDTO(
        room_id=message.room_id,
        user_id=message.user_id,
        content=message.content,
        edited=message.edited,
        id=message.id,
    )

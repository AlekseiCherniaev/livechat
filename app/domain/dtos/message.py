from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.message import Message


@dataclass
class MessagePublicDTO:
    room_id: UUID
    user_id: UUID
    username: str
    content: str
    edited: bool
    id: UUID
    created_at: datetime


def message_to_dto(message: Message, username: str) -> MessagePublicDTO:
    return MessagePublicDTO(
        room_id=message.room_id,
        user_id=message.user_id,
        username=username,
        content=message.content,
        edited=message.edited,
        id=message.id,
        created_at=message.created_at,
    )

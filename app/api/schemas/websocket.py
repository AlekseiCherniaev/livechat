from uuid import UUID

from pydantic import BaseModel


class TypingPayload(BaseModel):
    room_id: UUID
    is_typing: bool
    username: str

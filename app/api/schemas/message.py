from uuid import UUID

from pydantic import BaseModel, Field


class MessagePublic(BaseModel):
    room_id: UUID
    user_id: UUID
    username: str
    content: str
    edited: bool
    id: UUID


class SendMessageRequest(BaseModel):
    content: str = Field(max_length=256)


class EditMessageRequest(BaseModel):
    new_content: str = Field(max_length=256)

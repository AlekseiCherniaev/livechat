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
    user_id: UUID
    content: str = Field(max_length=256)


class EditMessageRequest(BaseModel):
    user_id: UUID
    new_content: str = Field(max_length=256)


class DeleteMessageRequest(BaseModel):
    user_id: UUID

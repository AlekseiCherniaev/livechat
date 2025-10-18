from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.dtos.join_request import JoinRequestCreateDTO
from app.domain.dtos.room import RoomCreateDTO, RoomUpdateDTO


class RoomCreate(BaseModel):
    name: str = Field(max_length=32)
    description: str | None = None
    is_public: bool = True

    def to_dto(self, created_by: UUID) -> RoomCreateDTO:
        return RoomCreateDTO(
            name=self.name,
            description=self.description,
            is_public=self.is_public,
            created_by=created_by,
        )


class RoomUpdate(BaseModel):
    description: str | None = None
    is_public: bool | None = None

    def to_dto(self, created_by: UUID) -> RoomUpdateDTO:
        return RoomUpdateDTO(
            description=self.description,
            is_public=self.is_public,
            created_by=created_by,
        )


class RoomPublic(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_public: bool
    created_by: UUID
    participants_count: int
    created_at: datetime
    updated_at: datetime


class SendJoinRequest(BaseModel):
    room_id: UUID
    message: str | None = None

    def to_dto(self, user_id: UUID) -> JoinRequestCreateDTO:
        return JoinRequestCreateDTO(
            room_id=self.room_id,
            user_id=user_id,
            message=self.message,
        )


class JoinRequestPublic(BaseModel):
    id: UUID
    message: str | None
    username: str
    room_name: str

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(max_length=32)


class UserCreate(UserBase):
    password: str = Field(max_length=32)


class UserLogin(UserBase):
    password: str = Field(max_length=32)


class UserPublic(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime | None

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserAuth(BaseModel):
    username: str = Field(max_length=32)
    password: str = Field(max_length=32)


class UserPublic(BaseModel):
    username: str
    last_active: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    id: UUID

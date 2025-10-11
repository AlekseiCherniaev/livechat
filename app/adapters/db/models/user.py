from datetime import datetime, timezone
from functools import partial
from uuid import UUID, uuid4

from sqlmodel import Field

from app.adapters.db.models.base import SQLModel
from app.domain.entities.user import User


class UserBase(SQLModel):
    username: str = Field(index=True)
    last_active_at: datetime | None = None


class UserModel(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str = Field()
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))

    def to_entity(self) -> User:
        return User(
            id=UUID(str(self.id)),
            username=self.username,
            hashed_password=self.hashed_password,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_active_at=self.last_active_at,
        )

    @classmethod
    def from_entity(cls, user: User) -> "UserModel":
        return cls(
            id=user.id,
            username=user.username,
            hashed_password=user.hashed_password,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_active_at=user.last_active_at,
        )


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: UUID


class UserUpdate(SQLModel):
    username: str | None = None
    password: str | None = None

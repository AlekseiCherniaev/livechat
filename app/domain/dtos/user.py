from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.user import User


@dataclass
class UserAuthDTO:
    username: str
    password: str


@dataclass
class UserPublicDTO:
    username: str
    last_active: datetime | None
    created_at: datetime
    updated_at: datetime
    id: UUID


def user_to_dto(user: User) -> UserPublicDTO:
    return UserPublicDTO(
        username=user.username,
        last_active=user.last_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        id=user.id,
    )

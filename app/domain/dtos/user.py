from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class UserAuthDTO:
    username: str
    password: str


@dataclass
class UserPublicDTO:
    username: str
    last_login_at: datetime | None
    last_active: datetime | None
    created_at: datetime
    updated_at: datetime
    id: UUID

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    username: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    id: str | None = None
    last_active_at: datetime | None = None

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: str
    username: str
    email: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime | None = None

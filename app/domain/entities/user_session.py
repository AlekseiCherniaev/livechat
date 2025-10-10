from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserSession:
    user_id: str
    room_id: str
    connected_at: datetime
    id: str | None = None
    disconnected_at: datetime | None = None

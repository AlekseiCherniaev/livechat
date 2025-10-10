from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserSession:
    id: str
    user_id: str
    room_id: str
    connected_at: datetime
    disconnected_at: datetime | None = None

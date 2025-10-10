from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    room_id: str
    user_id: str
    content: str
    timestamp: datetime
    id: str | None = None
    edited: bool = False

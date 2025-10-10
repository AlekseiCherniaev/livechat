from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    id: str
    room_id: str
    user_id: str
    content: str
    timestamp: datetime
    edited: bool = False

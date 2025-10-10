from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoomStats:
    room_id: str
    total_messages: int
    active_users: int
    last_updated: datetime

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class RoomStats:
    room_id: UUID
    total_messages: int
    users_amount: int
    last_updated: datetime

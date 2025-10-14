from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.constants import RoomRole


@dataclass
class RoomMembership:
    room_id: UUID
    user_id: UUID
    role: RoomRole
    joined_at: datetime
    last_active_at: datetime

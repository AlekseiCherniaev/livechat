from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.constants import JoinRequestStatus


@dataclass
class JoinRequestCreateDTO:
    message: str | None
    user_id: UUID
    room_id: UUID
    status: JoinRequestStatus = JoinRequestStatus.PENDING


@dataclass
class JoinRequestPublicDTO:
    room_id: UUID
    user_id: UUID
    status: JoinRequestStatus
    handled_by: UUID | None
    message: str | None
    created_at: datetime
    updated_at: datetime
    id: UUID

from dataclasses import dataclass
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
    message: str | None
    username: str
    room_name: str
    status: JoinRequestStatus = JoinRequestStatus.PENDING

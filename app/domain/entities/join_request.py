from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from uuid import uuid4, UUID

from app.core.constants import JoinRequestStatus


@dataclass
class JoinRequest:
    room_id: UUID
    user_id: UUID
    status: JoinRequestStatus
    handled_by: UUID | None = None
    message: str | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from uuid import uuid4, UUID


@dataclass
class JoinRequest:
    room_id: UUID
    user_id: UUID
    message: str | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

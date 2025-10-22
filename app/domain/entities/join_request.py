from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from uuid import UUID, uuid4


@dataclass
class JoinRequest:
    room_id: UUID
    user_id: UUID
    message: str | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, UTC))
    id: UUID = field(default_factory=uuid4)

from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from uuid import UUID, uuid4


@dataclass
class Message:
    room_id: UUID
    user_id: UUID
    content: str
    timestamp: datetime
    id: UUID = field(default_factory=uuid4)
    edited: bool = False
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))

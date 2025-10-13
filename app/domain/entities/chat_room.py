from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from uuid import uuid4, UUID


@dataclass
class ChatRoom:
    name: str
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)
    participants: list[UUID] = field(default_factory=list)

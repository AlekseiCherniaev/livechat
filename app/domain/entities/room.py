from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from uuid import uuid4, UUID


@dataclass
class Room:
    name: str
    description: str | None
    is_public: bool
    created_by: UUID
    participants_count: int = 0
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

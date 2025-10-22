from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from uuid import UUID, uuid4


@dataclass
class Room:
    name: str
    is_public: bool
    created_by: UUID
    participants_count: int = 0
    description: str | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, UTC))
    updated_at: datetime = field(default_factory=partial(datetime.now, UTC))
    id: UUID = field(default_factory=uuid4)

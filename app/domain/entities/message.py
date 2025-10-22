from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from uuid import UUID, uuid4


@dataclass
class Message:
    room_id: UUID
    user_id: UUID
    content: str
    edited: bool = False
    created_at: datetime = field(default_factory=partial(datetime.now, UTC))
    updated_at: datetime = field(default_factory=partial(datetime.now, UTC))
    id: UUID = field(default_factory=uuid4)

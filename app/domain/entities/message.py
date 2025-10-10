from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial


@dataclass
class Message:
    room_id: str
    user_id: str
    content: str
    timestamp: datetime
    id: str | None = None
    edited: bool = False
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))

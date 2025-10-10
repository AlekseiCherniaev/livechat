from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial


@dataclass
class ChatRoom:
    name: str
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: str | None = None
    participants: list[str] = field(default_factory=list)

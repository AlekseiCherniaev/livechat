from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatRoom:
    name: str
    created_at: datetime
    updated_at: datetime
    id: str | None = None
    participants: list[str] = field(default_factory=list)

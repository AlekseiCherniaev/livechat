from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatRoom:
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    participants: list[str] = field(default_factory=list)

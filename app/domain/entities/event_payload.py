from dataclasses import dataclass
from uuid import UUID


@dataclass
class EventPayload:
    user_id: UUID
    username: str
    timestamp: str
    content: str | None = None
    is_typing: bool | None = None

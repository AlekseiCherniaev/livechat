from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class EventPayload:
    timestamp: str
    user_id: UUID
    username: str
    payload: dict[str, Any] | None = None

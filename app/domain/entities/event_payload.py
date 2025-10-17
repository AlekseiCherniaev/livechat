from dataclasses import dataclass
from typing import Any


@dataclass
class EventPayload:
    timestamp: str
    username: str | None = None
    content: str | None = None
    is_typing: bool | None = None
    payload: dict[str, Any] | None = None

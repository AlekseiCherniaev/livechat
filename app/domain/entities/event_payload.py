from dataclasses import dataclass


@dataclass
class EventPayload:
    timestamp: str
    username: str | None = None
    content: str | None = None
    is_typing: bool | None = None
    payload: dict[str, str] | None = None

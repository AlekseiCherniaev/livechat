from dataclasses import dataclass


@dataclass
class EventPayload:
    timestamp: str
    payload: dict[str, str]

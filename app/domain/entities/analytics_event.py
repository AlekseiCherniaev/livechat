from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Any


@dataclass
class AnalyticsEvent:
    id: str
    event_type: Literal["message_sent", "user_joined", "user_left"]
    user_id: str
    room_id: str
    timestamp: datetime
    payload: dict[str, Any] | None = None

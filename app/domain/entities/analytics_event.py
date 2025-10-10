from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.constants import EventType


@dataclass
class AnalyticsEvent:
    event_type: EventType
    user_id: str
    room_id: str
    timestamp: datetime
    id: str | None = None
    payload: dict[str, Any] | None = None

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import EventType


@dataclass
class AnalyticsEvent:
    event_type: EventType
    user_id: UUID
    room_id: UUID
    timestamp: datetime
    id: UUID = field(default_factory=uuid4)
    payload: dict[str, Any] | None = None

from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import AnalyticsEventType


@dataclass
class AnalyticsEvent:
    event_type: AnalyticsEventType
    user_id: UUID
    room_id: UUID
    payload: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

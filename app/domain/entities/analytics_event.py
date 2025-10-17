from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import AnalyticsEventType


@dataclass
class AnalyticsEvent:
    event_type: AnalyticsEventType
    user_id: UUID | None = None
    room_id: UUID | None = None
    payload: dict[str, str] | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "user_id": self.user_id and str(self.user_id),
            "room_id": self.room_id and str(self.room_id),
            "payload": self.payload,
            "id": str(self.id),
        }

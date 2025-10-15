from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from functools import partial
from uuid import UUID, uuid4

from app.core.constants import AnalyticsEventType


@dataclass
class AnalyticsEvent:
    event_type: AnalyticsEventType
    user_id: UUID
    room_id: UUID
    payload: dict[str, str] | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, any]:
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["user_id"] = str(self.user_id)
        data["room_id"] = str(self.room_id)
        data["id"] = str(self.id)
        return data

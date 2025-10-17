from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import NotificationType


@dataclass
class Notification:
    user_id: UUID
    type: NotificationType
    payload: dict[str, str]
    read: bool = False
    source_id: UUID | None = None
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    updated_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)

    def to_payload(self) -> dict[str, Any]:
        data = {
            "user_id": str(self.user_id),
            "payload": self.payload,
            "read": self.read,
            "source_id": str(self.source_id),
            "id": str(self.id),
            "type": self.type.value,
        }
        return data

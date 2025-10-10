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
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: UUID = field(default_factory=uuid4)
    payload: dict[str, Any] | None = None
    read: bool = False

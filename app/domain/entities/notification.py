from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from typing import Any

from app.core.constants import NotificationType


@dataclass
class Notification:
    user_id: str
    type: NotificationType
    created_at: datetime = field(default_factory=partial(datetime.now, timezone.utc))
    id: str | None = None
    payload: dict[str, Any] | None = None
    read: bool = False

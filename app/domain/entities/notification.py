from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.constants import NotificationType


@dataclass
class Notification:
    user_id: str
    type: NotificationType
    created_at: datetime
    id: str | None = None
    payload: dict[str, Any] | None = None
    read: bool = False

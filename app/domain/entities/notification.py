from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.constants import NotificationType


@dataclass
class Notification:
    id: str
    user_id: str
    type: NotificationType
    created_at: datetime
    payload: dict[str, Any] | None = None
    read: bool = False

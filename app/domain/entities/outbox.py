from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.core.constants import OutboxMessageType, OutboxStatus


@dataclass
class Outbox:
    type: OutboxMessageType
    status: OutboxStatus
    payload: dict[str, Any]
    sent: bool = False
    dedup_key: str | None = None
    retries: int = 0
    max_retries: int = 5
    sent_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)

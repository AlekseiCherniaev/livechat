from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class WebSocketSession:
    user_id: UUID
    room_id: UUID
    connected_at: datetime
    last_ping_at: datetime
    id: UUID = field(default_factory=uuid4)
    disconnected_at: datetime | None = None

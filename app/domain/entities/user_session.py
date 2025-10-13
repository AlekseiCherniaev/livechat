from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class UserSession:
    user_id: UUID
    connected_at: datetime
    id: UUID = field(default_factory=uuid4)

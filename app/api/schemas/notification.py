from uuid import UUID

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    type: str
    payload: dict[str, str]
    read: bool
    source_id: UUID | None
    id: UUID


class NotificationListResponse(BaseModel):
    notifications: list[NotificationPublic]


class NotificationCountResponse(BaseModel):
    unread_count: int

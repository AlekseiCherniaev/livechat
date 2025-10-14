from typing import Protocol
from uuid import UUID

from app.domain.entities.message import Message
from app.domain.entities.notification import Notification


class NotificationRepository(Protocol):
    async def save(self, notification: Notification) -> None: ...

    async def create_notifications_for_room(
        self, room_id: UUID, message: Message
    ) -> None: ...

    async def get_user_notifications(
        self, user_id: UUID, unread_only: bool = False
    ) -> list[Notification]: ...

    async def list_recent(
        self, user_id: UUID, limit: int = 20
    ) -> list[Notification]: ...

    async def mark_as_read(self, notification_id: UUID) -> None: ...

    async def delete_by_user(self, user_id: UUID) -> None: ...

    async def count_unread(self, user_id: UUID) -> int: ...

    async def mark_all_as_read(self, user_id: UUID) -> None: ...

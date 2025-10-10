from typing import Protocol
from uuid import UUID

from app.domain.entities.message import Message
from app.domain.entities.notification import Notification


class NotificationRepository(Protocol):
    async def create(self, notification: Notification) -> None:
        pass

    async def create_notifications_for_room(
        self, room_id: UUID, message: Message
    ) -> None:
        """Notify all participants in the room except the sender."""
        pass

    async def get_user_notifications(
        self, user_id: UUID, unread_only: bool = False
    ) -> list[Notification]:
        pass

    async def mark_as_read(self, notification_id: UUID) -> None:
        pass

    async def delete_by_user(self, user_id: UUID) -> None:
        pass

    async def count_unread(self, user_id: UUID) -> int:
        pass

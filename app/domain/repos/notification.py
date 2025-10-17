from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.notification import Notification


class NotificationRepository(Protocol):
    async def save(
        self, notification: Notification, db_session: Any | None = None
    ) -> Notification: ...

    async def get_by_id(
        self, notification_id: UUID, db_session: Any | None = None
    ) -> Notification | None: ...

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool,
        limit: int,
        db_session: Any | None = None,
    ) -> list[Notification]: ...

    async def delete_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def count_unread(
        self, user_id: UUID, db_session: Any | None = None
    ) -> int: ...

    async def mark_as_read(
        self, notification_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def mark_all_as_read(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

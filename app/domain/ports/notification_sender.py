from typing import Protocol

from app.domain.entities.notification import Notification


class NotificationSenderPort(Protocol):
    async def send(self, notification: Notification) -> None: ...

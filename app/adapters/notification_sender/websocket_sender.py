from datetime import datetime, timezone

from app.core.constants import BroadcastEventType
from app.domain.entities.event_payload import EventPayload
from app.domain.entities.notification import Notification
from app.domain.ports.connection import ConnectionPort


class WebSocketNotificationSender:
    def __init__(self, connection_port: ConnectionPort):
        self._conn = connection_port

    async def send(self, notification: Notification) -> None:
        event_payload = EventPayload(
            payload={
                "notification_type": notification.type.value,
                "payload": notification.payload,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._conn.send_event_to_user(
            user_id=notification.user_id,
            event_type=BroadcastEventType.NOTIFICATION,
            event_payload=event_payload,
        )

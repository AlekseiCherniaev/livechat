from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.core.constants import (
    AnalyticsEventType,
    OutboxMessageType,
    OutboxStatus,
    BroadcastEventType,
)
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.message import Message
from app.domain.entities.outbox_event import OutboxEvent
from app.domain.exceptions.message import MessageNotFound, MessagePermissionError
from app.domain.ports.connection import ConnectionPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.message import MessageRepository
from app.domain.repos.outbox_event import OutboxEventRepository

logger = structlog.get_logger(__name__)


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        connection_port: ConnectionPort,
        outbox_repo: OutboxEventRepository,
        transaction_manager: TransactionManager,
    ):
        self._message_repo = message_repo
        self._connection_port = connection_port
        self._outbox_repo = outbox_repo
        self._tm = transaction_manager

    async def _create_outbox_event(
        self,
        event_type: AnalyticsEventType,
        user_id: UUID,
        room_id: UUID,
        payload: dict,
        dedup_key: str,
    ) -> None:
        analytics = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            room_id=room_id,
            payload=payload,
        )
        outbox = OutboxEvent(
            type=OutboxMessageType.ANALYTICS,
            status=OutboxStatus.PENDING,
            payload=analytics.to_payload(),
            dedup_key=dedup_key,
        )
        await self._outbox_repo.save(outbox)

    async def send_message(self, room_id: UUID, user_id: UUID, content: str) -> None:
        async def _txn():
            message = Message(
                room_id=room_id,
                user_id=user_id,
                content=content,
                timestamp=datetime.now(timezone.utc),
            )
            await self._message_repo.save(message=message)

            payload = {
                "id": str(message.id),
                "user_id": str(user_id),
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            }
            await self._connection_port.broadcast_event(
                room_id=room_id,
                event_type=BroadcastEventType.MESSAGE_CREATED,
                payload=payload,
            )

            await self._create_outbox_event(
                event_type=AnalyticsEventType.MESSAGE_SENT,
                user_id=user_id,
                room_id=room_id,
                payload={"message": content},
                dedup_key=f"message_sent:{message.id}",
            )
            logger.bind(message_id=message.id, room_id=room_id, user_id=user_id).info(
                "Message sent"
            )

        await self._tm.run_in_transaction(_txn)

    async def edit_message(
        self, message_id: UUID, user_id: UUID, new_content: str
    ) -> None:
        message = await self._message_repo.get_by_id(message_id=message_id)
        if not message:
            raise MessageNotFound

        if message.user_id != user_id:
            raise MessagePermissionError

        async def _txn():
            message.content = new_content
            message.edited = True
            message.updated_at = datetime.now(timezone.utc)
            await self._message_repo.save(message)

            payload = {
                "id": str(message.id),
                "user_id": str(user_id),
                "content": new_content,
                "timestamp": message.timestamp.isoformat(),
            }
            await self._connection_port.broadcast_event(
                room_id=message.room_id,
                event_type=BroadcastEventType.MESSAGE_EDITED,
                payload=payload,
            )

            await self._create_outbox_event(
                event_type=AnalyticsEventType.MESSAGE_EDITED,
                user_id=user_id,
                room_id=message.room_id,
                payload={"new_message": new_content},
                dedup_key=f"message_edited:{message.id}",
            )

            logger.bind(message_id=message.id).info("Message edited")

        await self._tm.run_in_transaction(_txn)

    async def delete_message(self, message_id: UUID, user_id: UUID) -> None:
        message = await self._message_repo.get_by_id(message_id=message_id)
        if not message:
            raise MessageNotFound

        if message.user_id != user_id:
            raise MessagePermissionError

        async def _txn():
            await self._message_repo.delete_by_id(message_id=message_id)

            payload = {
                "id": str(message.id),
                "user_id": str(user_id),
                "timestamp": message.timestamp.isoformat(),
            }
            await self._connection_port.broadcast_event(
                room_id=message.room_id,
                event_type=BroadcastEventType.MESSAGE_DELETED,
                payload=payload,
            )

            await self._create_outbox_event(
                event_type=AnalyticsEventType.MESSAGE_DELETED,
                user_id=user_id,
                room_id=message.room_id,
                payload={"message": message.content},
                dedup_key=f"message_deleted:{message.id}",
            )

            logger.bind(message_id=message.id).info("Message deleted")

        await self._tm.run_in_transaction(_txn)

    async def get_recent_messages(
        self, room_id: UUID, limit: int = 50
    ) -> list[Message]:
        return await self._message_repo.get_recent_by_room(room_id=room_id, limit=limit)

    async def get_messages_since(self, room_id: UUID, since: datetime) -> list[Message]:
        return await self._message_repo.get_since(room_id=room_id, since=since)

    async def get_user_messages(self, user_id: UUID, limit: int = 50) -> list[Message]:
        return await self._message_repo.list_by_user(user_id=user_id, limit=limit)

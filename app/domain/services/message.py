from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

from app.core.constants import (
    AnalyticsEventType,
    BroadcastEventType,
)
from app.domain.dtos.message import message_to_dto, MessagePublicDTO
from app.domain.entities.event_payload import EventPayload
from app.domain.entities.message import Message
from app.domain.exceptions.message import MessageNotFound, MessagePermissionError
from app.domain.exceptions.user import UserNotFound
from app.domain.ports.connection import ConnectionPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.message import MessageRepository
from app.domain.repos.outbox import OutboxRepository
from app.domain.repos.room_membership import RoomMembershipRepository
from app.domain.repos.user import UserRepository
from app.domain.services.utils import create_outbox_analytics_event

logger = structlog.get_logger(__name__)


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        user_repo: UserRepository,
        membership_repo: RoomMembershipRepository,
        outbox_repo: OutboxRepository,
        connection_port: ConnectionPort,
        transaction_manager: TransactionManager,
    ):
        self._message_repo = message_repo
        self._user_repo = user_repo
        self._membership_repo = membership_repo
        self._outbox_repo = outbox_repo
        self._connection_port = connection_port
        self._tm = transaction_manager

    async def send_message(self, room_id: UUID, user_id: UUID, content: str) -> None:
        user = await self._user_repo.get_by_id(user_id=user_id)
        if user is None:
            raise UserNotFound

        async def _txn(db_session: Any) -> Message:
            message = Message(
                room_id=room_id,
                user_id=user_id,
                content=content,
            )
            await self._message_repo.save(message=message, db_session=db_session)

            # If writing to the Outbox fails (e.g., Mongo is unavailable), the analytics event won't be sent,
            # but the Message itself is persisted. Missing events will be recovered later by the Outbox Repair Job.
            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.MESSAGE_SENT,
                user_id=user_id,
                room_id=room_id,
                payload={"message": content},
                dedup_key=f"message_sent:{message.id}",
                db_session=db_session,
            )

            logger.bind(message_id=message.id, room_id=room_id, user_id=user_id).info(
                "Message sent"
            )
            return message

        message_create: Message = await self._tm.run_in_transaction(_txn)
        payload = EventPayload(
            username=user.username,
            content=message_create.content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._connection_port.broadcast_event(
            room_id=room_id,
            event_type=BroadcastEventType.MESSAGE_CREATED,
            event_payload=payload,
        )

    async def edit_message(
        self, message_id: UUID, user_id: UUID, new_content: str
    ) -> None:
        user = await self._user_repo.get_by_id(user_id=user_id)
        if user is None:
            raise UserNotFound

        message = await self._message_repo.get_by_id(message_id=message_id)
        if not message:
            raise MessageNotFound

        if message.user_id != user_id:
            raise MessagePermissionError

        async def _txn(db_session: Any) -> Message:
            message.content = new_content
            message.edited = True
            message.updated_at = datetime.now(timezone.utc)
            await self._message_repo.save(message=message, db_session=db_session)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.MESSAGE_EDITED,
                user_id=user_id,
                room_id=message.room_id,
                payload={"new_message": new_content},
                dedup_key=f"message_edited:{message.id}",
                db_session=db_session,
            )

            logger.bind(message_id=message.id).info("Message edited")
            return message

        message_update: Message = await self._tm.run_in_transaction(_txn)
        payload = EventPayload(
            username=user.username,
            content=message_update.content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._connection_port.broadcast_event(
            room_id=message.room_id,
            event_type=BroadcastEventType.MESSAGE_EDITED,
            event_payload=payload,
        )

    async def delete_message(self, message_id: UUID, user_id: UUID) -> None:
        user = await self._user_repo.get_by_id(user_id=user_id)
        if user is None:
            raise UserNotFound

        message = await self._message_repo.get_by_id(message_id=message_id)
        if not message:
            raise MessageNotFound

        if message.user_id != user_id:
            raise MessagePermissionError

        async def _txn(db_session: Any) -> None:
            await self._message_repo.delete_by_id(
                message_id=message_id, db_session=db_session
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.MESSAGE_DELETED,
                user_id=user_id,
                room_id=message.room_id,
                payload={"message": message.content},
                dedup_key=f"message_deleted:{message.id}",
                db_session=db_session,
            )

            logger.bind(message_id=message.id).info("Message deleted")

        await self._tm.run_in_transaction(_txn)
        payload = EventPayload(
            username=user.username,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._connection_port.broadcast_event(
            room_id=message.room_id,
            event_type=BroadcastEventType.MESSAGE_DELETED,
            event_payload=payload,
        )

    async def get_recent_messages(
        self, room_id: UUID, user_id: UUID, limit: int
    ) -> list[MessagePublicDTO]:
        membership = await self._membership_repo.exists(
            room_id=room_id, user_id=user_id
        )
        if not membership:
            raise MessagePermissionError

        messages = await self._message_repo.get_recent_by_room(
            room_id=room_id, limit=limit
        )
        if not messages:
            return []

        user_ids = {msg.user_id for msg in messages}
        users = await self._user_repo.get_by_ids(user_ids=user_ids)
        users_map = {user.id: user.username for user in users}
        return [
            message_to_dto(message=msg, username=users_map.get(msg.user_id, "Unknown"))
            for msg in messages
        ]

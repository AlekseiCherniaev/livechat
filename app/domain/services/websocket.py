from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

from app.core.constants import AnalyticsEventType, BroadcastEventType
from app.domain.entities.event_payload import EventPayload
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.exceptions.room import RoomNotFound
from app.domain.exceptions.user import UserNotFound
from app.domain.exceptions.user_session import SessionNotFound, InvalidSession
from app.domain.exceptions.websocket_session import (
    WebSocketSessionNotFound,
    WebSocketSessionPermissionError,
)
from app.domain.ports.connection import ConnectionPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.outbox import OutboxRepository
from app.domain.repos.room import RoomRepository
from app.domain.repos.room_membership import RoomMembershipRepository
from app.domain.repos.user import UserRepository
from app.domain.repos.user_session import UserSessionRepository
from app.domain.repos.websocket_session import WebSocketSessionRepository
from app.domain.services.utils import create_outbox_analytics_event

logger = structlog.get_logger(__name__)


class WebSocketService:
    def __init__(
        self,
        ws_session_repo: WebSocketSessionRepository,
        user_repo: UserRepository,
        session_repo: UserSessionRepository,
        room_repo: RoomRepository,
        membership_repo: RoomMembershipRepository,
        outbox_repo: OutboxRepository,
        connection_port: ConnectionPort,
        transaction_manager: TransactionManager,
    ):
        self._ws_session_repo = ws_session_repo
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._room_repo = room_repo
        self._membership_repo = membership_repo
        self._outbox_repo = outbox_repo
        self._conn = connection_port
        self._tm = transaction_manager

    async def connect_to_room(self, session: WebSocketSession) -> list[str]:
        user = await self._user_repo.get_by_id(user_id=session.user_id)
        if not user:
            raise UserNotFound

        async def _txn(db_session: Any) -> None:
            await self._ws_session_repo.save(session=session, db_session=db_session)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_CONNECTED,
                user_id=session.user_id,
                room_id=session.room_id,
                dedup_key=f"user_connected:{session.id}",
                db_session=db_session,
            )
            logger.bind(session_id=session.id).info("WebSocket connected")

        await self._tm.run_in_transaction(_txn)

        await self._conn.connect_user_to_room(
            user_id=session.user_id, room_id=session.room_id
        )

        user_connections = await self._conn.get_user_connections(
            user_id=session.user_id
        )
        channels = [f"ws:user:{session.user_id}"] + [
            f"ws:room:{rid}" for rid in user_connections
        ]

        event = EventPayload(
            user_id=session.user_id,
            username=user.username,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._conn.broadcast_event(
            room_id=session.room_id,
            event_type=BroadcastEventType.ROOM_USER_ONLINE,
            event_payload=event,
        )
        return channels

    async def disconnect_from_room(self, session_id: UUID, user_id: UUID) -> None:
        session = await self._ws_session_repo.get_by_id(session_id=session_id)
        if not session:
            logger.debug("Disconnect called for unknown session", session_id=session_id)
            return

        if session.user_id != user_id:
            raise WebSocketSessionPermissionError

        user = await self._user_repo.get_by_id(user_id=session.user_id)
        if not user:
            raise UserNotFound

        async def _txn(db_session: Any) -> None:
            await self._ws_session_repo.delete_by_id(
                session_id=session_id, db_session=db_session
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_DISCONNECTED,
                user_id=session.user_id,
                room_id=session.room_id,
                dedup_key=f"user_disconnected:{session.id}",
                db_session=db_session,
            )

            logger.bind(session_id=session.id).info("WebSocket disconnected")

        await self._tm.run_in_transaction(_txn)

        await self._conn.disconnect_user_from_room(
            user_id=session.user_id, room_id=session.room_id
        )
        event = EventPayload(
            user_id=session.user_id,
            username=user.username,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._conn.broadcast_event(
            room_id=session.room_id,
            event_type=BroadcastEventType.ROOM_USER_OFFLINE,
            event_payload=event,
        )

    async def get_user_connections(self, user_id: UUID) -> set[UUID]:
        return await self._conn.get_user_connections(user_id=user_id)

    async def typing_indicator(
        self, room_id: UUID, user_id: UUID, username: str, is_typing: bool
    ) -> None:
        user = await self._user_repo.get_by_id(user_id=user_id)
        if not user:
            raise UserNotFound

        if user.username != username:
            raise WebSocketSessionPermissionError

        payload = {"is_typing": is_typing}
        event = EventPayload(
            user_id=user_id,
            username=username,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        await self._conn.broadcast_event(
            room_id=room_id,
            event_type=BroadcastEventType.USER_TYPING,
            event_payload=event,
        )

    async def update_ping(self, session_id: UUID, user_id: UUID) -> None:
        session = await self._ws_session_repo.get_by_id(session_id=session_id)
        if session is None:
            raise WebSocketSessionNotFound

        if session.user_id != user_id:
            raise WebSocketSessionPermissionError

        async def _txn(db_session: Any) -> None:
            await self._user_repo.update_last_active(
                user_id=session.user_id, db_session=db_session
            )
            await self._ws_session_repo.update_last_ping(
                session_id=session_id, db_session=db_session
            )

        await self._tm.run_in_transaction(_txn)

    async def active_users_in_room(self, room_id: UUID, user_id: UUID) -> list[UUID]:
        membership = await self._membership_repo.exists(
            room_id=room_id, user_id=user_id
        )
        if not membership:
            raise WebSocketSessionPermissionError

        return await self._conn.list_active_user_ids_in_room(room_id=room_id)

    async def disconnect_user_from_room(
        self, user_id: UUID, room_id: UUID, created_by: UUID
    ) -> None:
        room = await self._room_repo.get_by_id(room_id=room_id)
        if not room:
            raise RoomNotFound

        if room.created_by != created_by:
            raise WebSocketSessionPermissionError

        user = await self._user_repo.get_by_id(user_id=user_id)
        if not user:
            raise UserNotFound

        async def _txn(db_session: Any) -> None:
            sessions = await self._ws_session_repo.list_by_user_id(
                user_id=user_id, db_session=db_session
            )
            for s in sessions:
                if s.room_id == room_id:
                    await self._ws_session_repo.delete_by_id(
                        session_id=s.id, db_session=db_session
                    )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_FORCED_DISCONNECT,
                user_id=user_id,
                room_id=room_id,
                dedup_key=f"user_forced_disconnect:{user_id}:{room_id}",
                db_session=db_session,
            )

            logger.bind(user_id=user_id, room_id=room_id).info(
                "User disconnected from room by force"
            )

        await self._tm.run_in_transaction(_txn)
        await self._conn.disconnect_user_from_room(user_id=user_id, room_id=room_id)

    async def validate_user(self, session_id: str | None, room_id: UUID) -> UUID:
        if not session_id:
            raise SessionNotFound

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise InvalidSession

        session = await self._session_repo.get_by_id(session_id=session_uuid)
        if not session:
            raise SessionNotFound

        if not await self._membership_repo.exists(
            room_id=room_id, user_id=session.user_id
        ):
            raise WebSocketSessionPermissionError

        return session.user_id

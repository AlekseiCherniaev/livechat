from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.core.constants import AnalyticsEventType, BroadcastEventType
from app.domain.entities.user import User
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.exceptions.websocket_session import WebSocketSessionNotFound
from app.domain.ports.connection import ConnectionPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.outbox_event import OutboxEventRepository
from app.domain.repos.user import UserRepository
from app.domain.repos.websocket_session import WebSocketSessionRepository
from app.domain.services.utils import create_outbox_analytics_event

logger = structlog.get_logger(__name__)


class WebSocketService:
    def __init__(
        self,
        ws_session_repo: WebSocketSessionRepository,
        user_repo: UserRepository,
        outbox_repo: OutboxEventRepository,
        connection_port: ConnectionPort,
        transaction_manager: TransactionManager,
    ):
        self._ws_session_repo = ws_session_repo
        self._user_repo = user_repo
        self._outbox_repo = outbox_repo
        self._conn = connection_port
        self._tm = transaction_manager

    async def connect(self, session: WebSocketSession) -> None:
        async def _txn():
            await self._conn.connect(session)
            await self._ws_session_repo.save(session)
            await self._user_repo.update_last_active(session.user_id)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_CONNECTED,
                user_id=session.user_id,
                room_id=session.room_id,
                dedup_key=f"user_connected:{session.id}",
            )

            logger.bind(session_id=session.id).info("WebSocket connected")

        await self._tm.run_in_transaction(_txn)

    async def disconnect(self, session_id: UUID) -> None:
        session = await self._ws_session_repo.get(session_id)
        if not session:
            logger.debug("Disconnect called for unknown session", session_id=session_id)
            return

        async def _txn():
            await self._ws_session_repo.delete_by_id(session_id)
            await self._conn.disconnect(session_id)
            await self._user_repo.update_last_active(session.user_id)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_DISCONNECTED,
                user_id=session.user_id,
                room_id=session.room_id,
                dedup_key=f"user_disconnected:{session.id}",
            )

            logger.bind(session_id=session.session_id).info("WebSocket disconnected")

        await self._tm.run_in_transaction(_txn)

    async def typing_indicator(
        self, room_id: UUID, user_id: UUID, username: str, is_typing: bool
    ) -> None:
        payload = {
            "type": "user_typing",
            "user_id": str(user_id),
            "username": username,
            "is_typing": is_typing,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self._conn.broadcast_event(
            room_id=room_id, event_type=BroadcastEventType.USER_TYPING, payload=payload
        )

    async def update_ping(self, session_id: UUID) -> None:
        session = await self._ws_session_repo.get(session_id)
        if session is None:
            raise WebSocketSessionNotFound

        async def _txn():
            await self._ws_session_repo.update_last_ping(session_id)
            await self._conn.update_ping(session_id)
            await self._user_repo.update_last_active(session.user_id)

        await self._tm.run_in_transaction(_txn)

    async def list_users_in_room(self, room_id: UUID) -> list[User]:
        return await self._conn.list_users_in_room(room_id)

    async def disconnect_user_from_room(self, user_id: UUID, room_id: UUID) -> None:
        async def _txn():
            await self._conn.disconnect_user_from_room(user_id, room_id)
            sessions = await self._ws_session_repo.list_by_user_id(user_id)
            for s in sessions:
                if s.room_id == room_id:
                    await self._ws_session_repo.delete_by_id(s.id)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_FORCED_DISCONNECT,
                user_id=user_id,
                room_id=room_id,
                dedup_key=f"user_forced_disconnect:{user_id}:{room_id}",
            )

            logger.bind(user_id=user_id, room_id=room_id).info(
                "User disconnected from room by force"
            )

        await self._tm.run_in_transaction(_txn)

    async def is_user_online(self, user_id: UUID) -> bool:
        return await self._conn.is_user_online(user_id)

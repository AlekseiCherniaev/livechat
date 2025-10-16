from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, ANY
from uuid import uuid4

import pytest
from pytest_asyncio import fixture

from app.core.constants import AnalyticsEventType
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.exceptions.websocket_session import WebSocketSessionNotFound
from app.domain.services.websocket import WebSocketService


def make_session() -> WebSocketSession:
    now = datetime.now(timezone.utc)
    return WebSocketSession(
        user_id=uuid4(),
        room_id=uuid4(),
        session_id=uuid4(),
        connected_at=now,
        last_ping_at=now,
        ip_address="127.0.0.1",
    )


class TestWebSocketService:
    @fixture
    def service(self, ws_session_repo, user_repo, outbox_repo, connection_port, tm):
        return WebSocketService(
            ws_session_repo=ws_session_repo,
            user_repo=user_repo,
            outbox_repo=outbox_repo,
            connection_port=connection_port,
            transaction_manager=tm,
        )

    async def test_connect_success(
        self, service, ws_session_repo, user_repo, outbox_repo, connection_port, tm
    ):
        session = make_session()

        with patch(
            "app.domain.services.websocket.create_outbox_analytics_event",
            new=AsyncMock(),
        ) as create_event:
            await service.connect(session)

        tm.run_in_transaction.assert_awaited()
        user_repo.update_last_active.assert_awaited_with(
            user_id=session.user_id, db_session=ANY
        )
        ws_session_repo.save.assert_awaited_with(session=session, db_session=ANY)
        create_event.assert_awaited_with(
            outbox_repo=outbox_repo,
            event_type=AnalyticsEventType.USER_CONNECTED,
            user_id=session.user_id,
            room_id=session.room_id,
            dedup_key=f"user_connected:{session.id}",
            db_session=ANY,
        )
        connection_port.connect.assert_awaited_with(session=session)

    async def test_disconnect_success(
        self, service, ws_session_repo, user_repo, outbox_repo, connection_port, tm
    ):
        session = make_session()
        ws_session_repo.get_by_id.return_value = session

        with patch(
            "app.domain.services.websocket.create_outbox_analytics_event",
            new=AsyncMock(),
        ) as create_event:
            await service.disconnect(session.id)

        ws_session_repo.get_by_id.assert_awaited_with(session_id=session.id)
        user_repo.update_last_active.assert_awaited_with(
            user_id=session.user_id, db_session=ANY
        )
        ws_session_repo.delete_by_id.assert_awaited_with(
            session_id=session.id, db_session=ANY
        )
        create_event.assert_awaited_with(
            outbox_repo=outbox_repo,
            event_type=AnalyticsEventType.USER_DISCONNECTED,
            user_id=session.user_id,
            room_id=session.room_id,
            dedup_key=f"user_disconnected:{session.id}",
            db_session=ANY,
        )
        connection_port.disconnect.assert_awaited_with(session_id=session.id)

    async def test_disconnect_unknown_session(
        self, service, ws_session_repo, connection_port
    ):
        ws_session_repo.get_by_id.return_value = None
        session_id = uuid4()

        await service.disconnect(session_id)

        ws_session_repo.get_by_id.assert_awaited_with(session_id=session_id)
        connection_port.disconnect.assert_not_awaited()

    async def test_update_ping_success(
        self, service, ws_session_repo, user_repo, connection_port, tm
    ):
        session = make_session()
        ws_session_repo.get_by_id.return_value = session

        await service.update_ping(session.id)

        ws_session_repo.get_by_id.assert_awaited_with(session_id=session.id)
        user_repo.update_last_active.assert_awaited_with(
            user_id=session.user_id, db_session=ANY
        )
        ws_session_repo.update_last_ping.assert_awaited_with(
            session_id=session.id, db_session=ANY
        )
        connection_port.update_ping.assert_awaited_with(session_id=session.id)

    async def test_update_ping_not_found(self, service, ws_session_repo):
        ws_session_repo.get_by_id.return_value = None
        session_id = uuid4()

        with pytest.raises(WebSocketSessionNotFound):
            await service.update_ping(session_id)

        ws_session_repo.get_by_id.assert_awaited_with(session_id=session_id)

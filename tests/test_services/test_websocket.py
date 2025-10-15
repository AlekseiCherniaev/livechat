from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pytest_asyncio import fixture

from app.core.constants import BroadcastEventType
from app.domain.entities.user import User
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.exceptions.websocket_session import WebSocketSessionNotFound
from app.domain.services.websocket import WebSocketService


def any_dict_with_keys(expected_keys: set[str]):
    class Matcher:
        def __eq__(self, other):
            return isinstance(other, dict) and expected_keys.issubset(other.keys())

        def __repr__(self):
            return f"<AnyDictWithKeys {expected_keys}>"

    return Matcher()


class TestWebSocketService:
    @fixture
    def service(
        self, ws_session_repo, user_repo, outbox_repo, connection_port, tm
    ) -> WebSocketService:
        return WebSocketService(
            ws_session_repo=ws_session_repo,
            user_repo=user_repo,
            outbox_repo=outbox_repo,
            connection_port=connection_port,
            transaction_manager=tm,
        )

    async def test_connect_success(
        self, service, ws_session_repo, user_repo, connection_port, outbox_repo, tm
    ):
        session = WebSocketSession(
            user_id=uuid4(),
            room_id=uuid4(),
            connected_at=datetime.now(timezone.utc),
            last_ping_at=datetime.now(timezone.utc),
            session_id=uuid4(),
            ip_address="127.0.0.1",
        )

        await service.connect(session)

        tm.run_in_transaction.assert_awaited_once()
        connection_port.connect.assert_awaited_once_with(session)
        ws_session_repo.save.assert_awaited_once_with(session)
        user_repo.update_last_active.assert_awaited_once_with(session.user_id)
        outbox_repo.save.assert_awaited_once()

    async def test_disconnect_success(
        self, service, ws_session_repo, connection_port, user_repo, outbox_repo, tm
    ):
        session = WebSocketSession(
            user_id=uuid4(),
            room_id=uuid4(),
            connected_at=datetime.now(timezone.utc),
            last_ping_at=datetime.now(timezone.utc),
            session_id=uuid4(),
            ip_address="127.0.0.1",
        )
        ws_session_repo.get.return_value = session

        await service.disconnect(session.id)

        ws_session_repo.get.assert_awaited_once_with(session.id)
        tm.run_in_transaction.assert_awaited_once()
        ws_session_repo.delete_by_id.assert_awaited_once_with(session.id)
        connection_port.disconnect.assert_awaited_once_with(session.id)
        user_repo.update_last_active.assert_awaited_once_with(session.user_id)
        outbox_repo.save.assert_awaited_once()

    async def test_disconnect_not_found(self, service, ws_session_repo, tm):
        ws_session_repo.get.return_value = None

        await service.disconnect(uuid4())

        tm.run_in_transaction.assert_not_awaited()

    async def test_typing_indicator_success(self, service, connection_port):
        room_id = uuid4()
        user_id = uuid4()
        username = "alice"

        await service.typing_indicator(room_id, user_id, username, is_typing=True)

        connection_port.broadcast_event.assert_awaited_once_with(
            room_id=room_id,
            event_type=BroadcastEventType.USER_TYPING,
            payload=any_dict_with_keys(
                {"type", "user_id", "username", "is_typing", "timestamp"}
            ),
        )

    async def test_update_ping_success(
        self, service, ws_session_repo, connection_port, user_repo, tm
    ):
        session_id = uuid4()
        session = WebSocketSession(
            user_id=uuid4(),
            room_id=uuid4(),
            connected_at=datetime.now(timezone.utc),
            last_ping_at=datetime.now(timezone.utc),
            session_id=session_id,
            ip_address="127.0.0.1",
        )
        ws_session_repo.get.return_value = session

        await service.update_ping(session_id)

        ws_session_repo.get.assert_awaited_once_with(session_id)
        tm.run_in_transaction.assert_awaited_once()
        ws_session_repo.update_last_ping.assert_awaited_once_with(session_id)
        connection_port.update_ping.assert_awaited_once_with(session_id)
        user_repo.update_last_active.assert_awaited_once_with(session.user_id)

    async def test_update_ping_not_found(self, service, ws_session_repo):
        ws_session_repo.get.return_value = None
        with pytest.raises(WebSocketSessionNotFound):
            await service.update_ping(uuid4())

    async def test_list_users_in_room_success(self, service, connection_port):
        room_id = uuid4()
        users = [User(username="bob", id=uuid4(), hashed_password="x")]
        connection_port.list_users_in_room.return_value = users

        result = await service.list_users_in_room(room_id)

        assert result == users
        connection_port.list_users_in_room.assert_awaited_once_with(room_id)

    async def test_disconnect_user_from_room_success(
        self, service, ws_session_repo, connection_port, outbox_repo, tm
    ):
        user_id = uuid4()
        room_id = uuid4()
        sessions = [
            WebSocketSession(
                user_id=user_id,
                room_id=room_id,
                connected_at=datetime.now(timezone.utc),
                last_ping_at=datetime.now(timezone.utc),
                session_id=uuid4(),
                ip_address="127.0.0.1",
            )
        ]
        ws_session_repo.list_by_user_id.return_value = sessions

        await service.disconnect_user_from_room(user_id, room_id)

        tm.run_in_transaction.assert_awaited_once()
        connection_port.disconnect_user_from_room.assert_awaited_once_with(
            user_id, room_id
        )
        ws_session_repo.list_by_user_id.assert_awaited_once_with(user_id)
        ws_session_repo.delete_by_id.assert_awaited_once_with(sessions[0].id)
        outbox_repo.save.assert_awaited_once()

    async def test_is_user_online(self, service, connection_port):
        user_id = uuid4()
        connection_port.is_user_online.return_value = True

        result = await service.is_user_online(user_id)

        assert result is True
        connection_port.is_user_online.assert_awaited_once_with(user_id)

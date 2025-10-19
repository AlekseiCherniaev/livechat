from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pytest_asyncio import fixture

from app.core.constants import BroadcastEventType
from app.domain.entities.message import Message
from app.domain.entities.user import User
from app.domain.exceptions.message import (
    MessageNotFound,
    MessagePermissionError,
)
from app.domain.exceptions.user import UserNotFound
from app.domain.services.message import MessageService


class TestMessageService:
    @fixture
    def service(
        self, message_repo, user_repo, membership_repo, connection_port, outbox_repo, tm
    ):
        return MessageService(
            message_repo=message_repo,
            user_repo=user_repo,
            membership_repo=membership_repo,
            connection_port=connection_port,
            outbox_repo=outbox_repo,
            transaction_manager=tm,
        )

    async def test_send_message_success(
        self, service, message_repo, user_repo, connection_port
    ):
        user_id = uuid4()
        room_id = uuid4()
        user_repo.get_by_id.return_value = AsyncMock(username="john")

        async def save_message(message, db_session):
            message.id = uuid4()
            return message

        message_repo.save.side_effect = save_message

        await service.send_message(room_id=room_id, user_id=user_id, content="hi")

        user_repo.get_by_id.assert_awaited_once_with(user_id=user_id)
        message_repo.save.assert_awaited()
        connection_port.broadcast_event.assert_awaited_once()
        args, kwargs = connection_port.broadcast_event.await_args
        assert kwargs["room_id"] == room_id
        assert kwargs["event_type"] == BroadcastEventType.MESSAGE_CREATED

    async def test_send_message_user_not_found(self, service, user_repo):
        user_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFound):
            await service.send_message(uuid4(), uuid4(), "hello")

    async def test_edit_message_success(
        self, service, message_repo, user_repo, connection_port
    ):
        user_id = uuid4()
        room_id = uuid4()
        msg_id = uuid4()
        user_repo.get_by_id.return_value = AsyncMock(username="john")
        message_repo.get_by_id.return_value = Message(
            id=msg_id,
            room_id=room_id,
            user_id=user_id,
            content="old",
            created_at=datetime.now(timezone.utc),
        )

        await service.edit_message(msg_id, user_id, "new content")

        message_repo.save.assert_awaited()
        connection_port.broadcast_event.assert_awaited_once()
        args, kwargs = connection_port.broadcast_event.await_args
        assert kwargs["event_type"] == BroadcastEventType.MESSAGE_EDITED

    async def test_edit_message_user_not_found(self, service, user_repo):
        user_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFound):
            await service.edit_message(uuid4(), uuid4(), "new")

    async def test_edit_message_not_found(self, service, user_repo, message_repo):
        user_repo.get_by_id.return_value = AsyncMock(username="john")
        message_repo.get_by_id.return_value = None
        with pytest.raises(MessageNotFound):
            await service.edit_message(uuid4(), uuid4(), "edit")

    async def test_edit_message_permission_error(
        self, service, user_repo, message_repo
    ):
        user_id = uuid4()
        message_repo.get_by_id.return_value = Message(
            id=uuid4(),
            room_id=uuid4(),
            user_id=uuid4(),
            content="hello",
            created_at=datetime.now(timezone.utc),
        )
        user_repo.get_by_id.return_value = AsyncMock(username="john")

        with pytest.raises(MessagePermissionError):
            await service.edit_message(uuid4(), user_id, "new text")

    async def test_delete_message_success(
        self, service, user_repo, message_repo, connection_port
    ):
        user_id = uuid4()
        room_id = uuid4()
        msg_id = uuid4()
        message = Message(
            id=msg_id,
            room_id=room_id,
            user_id=user_id,
            content="bye",
            created_at=datetime.now(timezone.utc),
        )
        user_repo.get_by_id.return_value = AsyncMock(username="john")
        message_repo.get_by_id.return_value = message

        await service.delete_message(msg_id, user_id)

        message_repo.delete_by_id.assert_awaited_once()
        connection_port.broadcast_event.assert_awaited_once()
        args, kwargs = connection_port.broadcast_event.await_args
        assert kwargs["event_type"] == BroadcastEventType.MESSAGE_DELETED

    async def test_delete_message_user_not_found(self, service, user_repo):
        user_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFound):
            await service.delete_message(uuid4(), uuid4())

    async def test_delete_message_not_found(self, service, user_repo, message_repo):
        user_repo.get_by_id.return_value = AsyncMock(username="john")
        message_repo.get_by_id.return_value = None
        with pytest.raises(MessageNotFound):
            await service.delete_message(uuid4(), uuid4())

    async def test_delete_message_permission_error(
        self, service, user_repo, message_repo
    ):
        user_id = uuid4()
        message_repo.get_by_id.return_value = Message(
            id=uuid4(),
            room_id=uuid4(),
            user_id=uuid4(),
            content="bye",
            created_at=datetime.now(timezone.utc),
        )
        user_repo.get_by_id.return_value = AsyncMock(username="john")

        with pytest.raises(MessagePermissionError):
            await service.delete_message(uuid4(), user_id)

    async def test_get_recent_messages(self, service, message_repo, membership_repo):
        room_id = uuid4()
        user_id = uuid4()
        membership_repo.list_users.return_value = [
            User(
                id=user_id,
                username="test",
                hashed_password="test",
            )
        ]
        message_repo.get_recent_by_room.return_value = [
            Message(
                id=uuid4(),
                room_id=room_id,
                user_id=user_id,
                content="hello",
                created_at=datetime.now(timezone.utc),
            )
        ]

        result = await service.get_recent_messages(
            room_id=room_id, user_id=user_id, limit=5, before=None
        )

        message_repo.get_recent_by_room.assert_awaited_once_with(
            room_id=room_id, limit=5, before=None
        )
        assert len(result) == 1
        assert result[0].content == "hello"

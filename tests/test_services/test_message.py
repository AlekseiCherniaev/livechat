from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.constants import BroadcastEventType
from app.domain.entities.message import Message
from app.domain.entities.user import User
from app.domain.exceptions.message import MessageNotFound, MessagePermissionError
from app.domain.exceptions.user import UserNotFound
from app.domain.services.message import MessageService


@pytest.fixture
def service(message_repo, user_repo, membership_repo, connection_port, outbox_repo, tm):
    return MessageService(
        message_repo=message_repo,
        user_repo=user_repo,
        membership_repo=membership_repo,
        connection_port=connection_port,
        outbox_repo=outbox_repo,
        transaction_manager=tm,
    )


@pytest.fixture
def sample_user():
    return User(id=uuid4(), username="john", hashed_password="hashed-pass")


@pytest.fixture
def sample_message(sample_user):
    return Message(
        id=uuid4(),
        room_id=uuid4(),
        user_id=sample_user.id,
        content="hello",
        created_at=datetime.now(UTC),
    )


class TestMessageService:
    async def test_send_message_success(
        self,
        service,
        message_repo,
        user_repo,
        membership_repo,
        connection_port,
        sample_user,
    ):
        room_id = uuid4()
        user_repo.get_by_id.return_value = sample_user
        membership_repo.exists.return_value = True

        saved_message = Message(room_id=room_id, user_id=sample_user.id, content="hi")
        saved_message.id = uuid4()
        message_repo.save.return_value = saved_message

        result = await service.send_message(
            room_id=room_id, user_id=sample_user.id, content="hi"
        )

        user_repo.get_by_id.assert_awaited_once_with(user_id=sample_user.id)
        membership_repo.exists.assert_awaited_once_with(
            room_id=room_id, user_id=sample_user.id
        )
        message_repo.save.assert_awaited()
        service._tm.run_in_transaction.assert_awaited()
        connection_port.broadcast_event.assert_awaited_once()
        _, kwargs = connection_port.broadcast_event.await_args
        assert kwargs["room_id"] == room_id
        assert kwargs["event_type"] == BroadcastEventType.MESSAGE_CREATED
        assert "message" in kwargs["event_payload"].payload
        assert kwargs["event_payload"].payload["user_id"] == str(sample_user.id)
        assert result.content == "hi"
        assert result.username == "john"

    @pytest.mark.parametrize(
        ("user_exists", "membership_exists", "expected_exception"),
        [
            (None, True, UserNotFound),
            (AsyncMock(), False, MessagePermissionError),
        ],
    )
    async def test_validate_user_failures(
        self,
        service,
        user_repo,
        membership_repo,
        user_exists,
        membership_exists,
        expected_exception,
    ):
        user_id, room_id = uuid4(), uuid4()
        user_repo.get_by_id.return_value = user_exists
        membership_repo.exists.return_value = membership_exists
        with pytest.raises(expected_exception):
            await service._validate_user(user_id=user_id, room_id=room_id)

    async def test_edit_message_success(
        self,
        service,
        message_repo,
        user_repo,
        membership_repo,
        connection_port,
        sample_message,
        sample_user,
    ):
        new_content = "new content"
        message_repo.get_by_id.return_value = sample_message
        user_repo.get_by_id.return_value = sample_user
        membership_repo.exists.return_value = True

        result = await service.edit_message(
            sample_message.id, sample_user.id, new_content
        )

        message_repo.save.assert_awaited()
        connection_port.broadcast_event.assert_awaited_once()
        _, kwargs = connection_port.broadcast_event.await_args
        assert kwargs["event_type"] == BroadcastEventType.MESSAGE_EDITED
        assert kwargs["room_id"] == sample_message.room_id
        assert kwargs["event_payload"].payload["message"] == new_content
        assert result.content == new_content
        assert result.username == "john"

    async def test_edit_message_not_found(self, service, message_repo, user_repo):
        user_repo.get_by_id.return_value = AsyncMock()
        message_repo.get_by_id.return_value = None
        with pytest.raises(MessageNotFound):
            await service.edit_message(uuid4(), uuid4(), "edit")

    async def test_edit_message_permission_error(
        self,
        service,
        message_repo,
        user_repo,
        membership_repo,
        sample_message,
        sample_user,
    ):
        other_user_id = uuid4()
        user_repo.get_by_id.return_value = sample_user
        message_repo.get_by_id.return_value = sample_message
        membership_repo.exists.return_value = False
        with pytest.raises(MessagePermissionError):
            await service.edit_message(sample_message.id, other_user_id, "new text")

    async def test_delete_message_success(
        self,
        service,
        message_repo,
        user_repo,
        membership_repo,
        connection_port,
        sample_message,
        sample_user,
    ):
        message_repo.get_by_id.return_value = sample_message
        user_repo.get_by_id.return_value = sample_user
        membership_repo.exists.return_value = True

        await service.delete_message(sample_message.id, sample_user.id)

        membership_repo.exists.assert_awaited_once_with(
            room_id=sample_message.room_id, user_id=sample_user.id
        )
        message_repo.delete_by_id.assert_awaited_once()
        service._tm.run_in_transaction.assert_awaited()
        connection_port.broadcast_event.assert_awaited_once()
        _, kwargs = connection_port.broadcast_event.await_args
        assert kwargs["event_type"] == BroadcastEventType.MESSAGE_DELETED
        assert kwargs["room_id"] == sample_message.room_id
        assert kwargs["event_payload"].payload["message"] == sample_message.content

    @pytest.mark.parametrize(
        ("user_exists", "message_exists", "expected_exception"),
        [
            (None, True, UserNotFound),
            (True, None, MessageNotFound),
        ],
    )
    async def test_delete_message_failures(
        self,
        service,
        user_repo,
        message_repo,
        membership_repo,
        sample_message,
        user_exists,
        message_exists,
        expected_exception,
    ):
        user_repo.get_by_id.return_value = AsyncMock() if user_exists else None
        message_repo.get_by_id.return_value = sample_message if message_exists else None
        membership_repo.exists.return_value = True
        with pytest.raises(expected_exception):
            await service.delete_message(uuid4(), uuid4())

    async def test_delete_message_permission_error(
        self,
        service,
        user_repo,
        membership_repo,
        message_repo,
        sample_message,
        sample_user,
    ):
        message_repo.get_by_id.return_value = sample_message
        user_repo.get_by_id.return_value = sample_user
        membership_repo.exists.return_value = False
        with pytest.raises(MessagePermissionError):
            await service.delete_message(sample_message.id, sample_user.id)

    async def test_get_recent_messages_success(
        self, service, message_repo, membership_repo, user_repo, sample_user
    ):
        room_id = uuid4()
        user_id = sample_user.id
        membership_repo.exists.return_value = True
        message = Message(
            id=uuid4(),
            room_id=room_id,
            user_id=user_id,
            content="hello",
            created_at=datetime.now(UTC),
        )
        message_repo.get_recent_by_room.return_value = [message]
        user_repo.get_by_ids.return_value = [sample_user]

        result = await service.get_recent_messages(
            room_id, user_id, limit=5, before=None
        )

        message_repo.get_recent_by_room.assert_awaited_once_with(
            room_id=room_id, limit=5, before=None
        )
        user_repo.get_by_ids.assert_awaited_once()
        assert len(result) == 1
        assert result[0].content == "hello"
        assert result[0].username == "john"

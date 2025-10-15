from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pytest_asyncio import fixture

from app.core.constants import BroadcastEventType
from app.domain.entities.message import Message
from app.domain.exceptions.message import MessageNotFound, MessagePermissionError
from app.domain.services.message import MessageService


def any_dict_with_keys(expected_keys: set[str]):
    class Matcher:
        def __eq__(self, other):
            return isinstance(other, dict) and expected_keys.issubset(other.keys())

        def __repr__(self):
            return f"<AnyDictWithKeys {expected_keys}>"

    return Matcher()


class TestMessageService:
    @fixture
    def service(self, message_repo, connection_port, outbox_repo, tm) -> MessageService:
        return MessageService(
            message_repo=message_repo,
            connection_port=connection_port,
            outbox_repo=outbox_repo,
            transaction_manager=tm,
        )

    async def test_send_message_success(
        self, service, message_repo, connection_port, outbox_repo, tm
    ):
        room_id = uuid4()
        user_id = uuid4()
        content = "Hello world"

        message_repo.save.side_effect = lambda message: message

        await service.send_message(room_id, user_id, content)

        tm.run_in_transaction.assert_awaited_once()
        message_repo.save.assert_awaited_once()
        connection_port.broadcast_event.assert_awaited_once_with(
            room_id=room_id,
            event_type=BroadcastEventType.MESSAGE_CREATED,
            payload=any_dict_with_keys({"id", "user_id", "content", "timestamp"}),
        )
        outbox_repo.save.assert_awaited_once()

    async def test_edit_message_success(
        self, service, message_repo, connection_port, outbox_repo, tm
    ):
        user_id = uuid4()
        message = Message(
            room_id=uuid4(),
            user_id=user_id,
            content="Old message",
            timestamp=datetime.now(timezone.utc),
            id=uuid4(),
        )
        new_content = "Updated message"

        message_repo.get_by_id.return_value = message
        message_repo.save.side_effect = lambda m: m

        await service.edit_message(
            message_id=message.id, user_id=user_id, new_content=new_content
        )

        tm.run_in_transaction.assert_awaited_once()
        message_repo.save.assert_awaited_once()
        connection_port.broadcast_event.assert_awaited_once_with(
            room_id=message.room_id,
            event_type=BroadcastEventType.MESSAGE_EDITED,
            payload=any_dict_with_keys({"id", "user_id", "content", "timestamp"}),
        )
        outbox_repo.save.assert_awaited_once()
        assert message.edited is True
        assert message.content == new_content

    async def test_edit_message_not_found(self, service, message_repo):
        message_repo.get_by_id.return_value = None
        with pytest.raises(MessageNotFound):
            await service.edit_message(uuid4(), uuid4(), "new")

    async def test_edit_message_permission_error(self, service, message_repo):
        message_repo.get_by_id.return_value = Message(
            room_id=uuid4(),
            user_id=uuid4(),
            content="Hi",
            timestamp=datetime.now(timezone.utc),
        )
        with pytest.raises(MessagePermissionError):
            await service.edit_message(uuid4(), uuid4(), "new")

    async def test_delete_message_success(
        self, service, message_repo, connection_port, outbox_repo, tm
    ):
        user_id = uuid4()
        message = Message(
            room_id=uuid4(),
            user_id=user_id,
            content="Message to delete",
            timestamp=datetime.now(timezone.utc),
            id=uuid4(),
        )

        message_repo.get_by_id.return_value = message

        await service.delete_message(message_id=message.id, user_id=user_id)

        tm.run_in_transaction.assert_awaited_once()
        message_repo.delete_by_id.assert_awaited_once_with(message_id=message.id)
        connection_port.broadcast_event.assert_awaited_once_with(
            room_id=message.room_id,
            event_type=BroadcastEventType.MESSAGE_DELETED,
            payload=any_dict_with_keys({"id", "user_id", "timestamp"}),
        )
        outbox_repo.save.assert_awaited_once()

    async def test_delete_message_not_found(self, service, message_repo):
        message_repo.get_by_id.return_value = None
        with pytest.raises(MessageNotFound):
            await service.delete_message(uuid4(), uuid4())

    async def test_delete_message_permission_error(self, service, message_repo):
        message_repo.get_by_id.return_value = Message(
            room_id=uuid4(),
            user_id=uuid4(),
            content="Test",
            timestamp=datetime.now(timezone.utc),
        )
        with pytest.raises(MessagePermissionError):
            await service.delete_message(uuid4(), uuid4())

    async def test_get_recent_messages(self, service, message_repo):
        room_id = uuid4()
        messages = [
            Message(
                room_id=room_id,
                user_id=uuid4(),
                content="A",
                timestamp=datetime.now(timezone.utc),
            )
        ]
        message_repo.get_recent_by_room.return_value = messages

        result = await service.get_recent_messages(room_id, limit=10)

        assert result == messages
        message_repo.get_recent_by_room.assert_awaited_once_with(
            room_id=room_id, limit=10
        )

    async def test_get_messages_since(self, service, message_repo):
        room_id = uuid4()
        since = datetime.now(timezone.utc)
        messages = [
            Message(room_id=room_id, user_id=uuid4(), content="B", timestamp=since)
        ]
        message_repo.get_since.return_value = messages

        result = await service.get_messages_since(room_id, since)

        assert result == messages
        message_repo.get_since.assert_awaited_once_with(room_id=room_id, since=since)

    async def test_get_user_messages(self, service, message_repo):
        user_id = uuid4()
        messages = [
            Message(
                room_id=uuid4(),
                user_id=user_id,
                content="C",
                timestamp=datetime.now(timezone.utc),
            )
        ]
        message_repo.list_by_user.return_value = messages

        result = await service.get_user_messages(user_id, limit=5)

        assert result == messages
        message_repo.list_by_user.assert_awaited_once_with(user_id=user_id, limit=5)

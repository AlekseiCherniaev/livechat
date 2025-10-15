import pytest
from pytest_asyncio import fixture
from uuid import uuid4

from app.core.constants import NotificationType
from app.domain.entities.notification import Notification
from app.domain.exceptions.notification import NotificationNotFound
from app.domain.services.notification import NotificationService


class TestNotificationService:
    @fixture
    def service(self, notif_repo, outbox_repo, tm) -> NotificationService:
        return NotificationService(
            notification_repo=notif_repo,
            outbox_repo=outbox_repo,
            transaction_manager=tm,
        )

    async def test_list_user_notifications_success(self, service, notif_repo):
        user_id = uuid4()
        notif_repo.get_user_notifications.return_value = [
            Notification(
                id=uuid4(),
                user_id=user_id,
                payload={"msg": "hi"},
                read=False,
                type=NotificationType.MESSAGE_SENT,
            )
        ]

        result = await service.list_user_notifications(user_id=user_id)

        notif_repo.get_user_notifications.assert_awaited_once_with(
            user_id=user_id, unread_only=False
        )
        assert len(result) == 1
        assert result[0].payload["msg"] == "hi"

    async def test_list_user_notifications_unread_only(self, service, notif_repo):
        user_id = uuid4()
        notif_repo.get_user_notifications.return_value = []

        result = await service.list_user_notifications(
            user_id=user_id, unread_only=True
        )

        notif_repo.get_user_notifications.assert_awaited_once_with(
            user_id=user_id, unread_only=True
        )
        assert result == []

    async def test_mark_as_read_success(self, service, notif_repo, tm):
        notif_id = uuid4()
        notification = Notification(
            id=notif_id,
            user_id=uuid4(),
            payload={"msg": "test"},
            read=False,
            type=NotificationType.MESSAGE_SENT,
        )
        notif_repo.get_by_id.return_value = notification

        await service.mark_as_read(notif_id)

        notif_repo.get_by_id.assert_awaited_once_with(notification_id=notif_id)
        tm.run_in_transaction.assert_awaited_once()
        service._outbox_repo.save.assert_awaited()

    async def test_mark_as_read_not_found(self, service, notif_repo):
        notif_id = uuid4()
        notif_repo.get_by_id.return_value = None

        with pytest.raises(NotificationNotFound):
            await service.mark_as_read(notif_id)

    async def test_mark_all_as_read_success(self, service, notif_repo, tm):
        user_id = uuid4()

        await service.mark_all_as_read(user_id)

        tm.run_in_transaction.assert_awaited_once()
        notif_repo.mark_all_as_read.assert_awaited_once_with(user_id)
        service._outbox_repo.save.assert_awaited()

    async def test_count_unread_success(self, service, notif_repo):
        user_id = uuid4()
        notif_repo.count_unread.return_value = 3

        count = await service.count_unread(user_id)

        notif_repo.count_unread.assert_awaited_once_with(user_id)
        assert count == 3

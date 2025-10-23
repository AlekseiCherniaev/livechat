from unittest.mock import AsyncMock

from pytest_asyncio import fixture

from app.domain.ports.analytics import AnalyticsPort
from app.domain.ports.cache import CachePort
from app.domain.ports.connection import ConnectionPort
from app.domain.ports.notification_sender import NotificationSenderPort
from app.domain.ports.password_hasher import PasswordHasherPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.join_request import JoinRequestRepository
from app.domain.repos.message import MessageRepository
from app.domain.repos.notification import NotificationRepository
from app.domain.repos.outbox import OutboxRepository
from app.domain.repos.room import RoomRepository
from app.domain.repos.room_membership import RoomMembershipRepository
from app.domain.repos.user import UserRepository
from app.domain.repos.user_session import UserSessionRepository
from app.domain.repos.websocket_session import WebSocketSessionRepository


@fixture
def room_repo():
    return AsyncMock(spec=RoomRepository)


@fixture
def ws_session_repo():
    return AsyncMock(spec=WebSocketSessionRepository)


@fixture
def user_repo():
    return AsyncMock(spec=UserRepository)


@fixture
def session_repo():
    return AsyncMock(spec=UserSessionRepository)


@fixture
def join_repo():
    return AsyncMock(spec=JoinRequestRepository)


@fixture
def membership_repo():
    return AsyncMock(spec=RoomMembershipRepository)


@fixture
def message_repo():
    return AsyncMock(spec=MessageRepository)


@fixture
def notif_repo():
    return AsyncMock(spec=NotificationRepository)


@fixture
def outbox_repo():
    return AsyncMock(spec=OutboxRepository)


@fixture
def analytics_port():
    return AsyncMock(spec=AnalyticsPort)


@fixture
def notification_port():
    return AsyncMock(spec=NotificationSenderPort)


@fixture
def connection_port():
    return AsyncMock(spec=ConnectionPort)


@fixture
def cache_port():
    return AsyncMock(spec=CachePort)


@fixture
def password_hasher():
    hasher = AsyncMock(spec=PasswordHasherPort)
    hasher.hash.side_effect = lambda password: f"hashed-{password}"
    hasher.verify.side_effect = (
        lambda *, password, hashed: hashed == f"hashed-{password}"
    )
    return hasher


@fixture
def tm():
    tm = AsyncMock(spec=TransactionManager)
    db_session = AsyncMock()

    async def _run_in_txn(fn, *a, **kw):
        return await fn(db_session, *a, **kw)

    tm.run_in_transaction.side_effect = _run_in_txn
    return tm

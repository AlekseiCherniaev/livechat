from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4, UUID

import pytest

from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.user_session import SessionNotFound, InvalidSession
from app.domain.exceptions.user import (
    UserAlreadyExists,
    UserInvalidCredentials,
    UserNotFound,
)
from app.domain.ports.password_hasher import PasswordHasherPort
from app.domain.repos.user_session import UserSessionRepository
from app.domain.repos.user import UserRepository
from app.domain.services.user_service import UserService


@pytest.mark.asyncio
class TestUserService:
    @pytest.fixture
    def user_repo(self) -> UserRepository:
        repo = AsyncMock(spec=UserRepository)
        return repo

    @pytest.fixture
    def session_repo(self) -> UserSessionRepository:
        repo = AsyncMock(spec=UserSessionRepository)
        return repo

    @pytest.fixture
    def password_hasher(self) -> PasswordHasherPort:
        hasher = AsyncMock(spec=PasswordHasherPort)
        hasher.hash.side_effect = lambda password: f"hashed-{password}"
        hasher.verify.side_effect = lambda plain, hashed: hashed == f"hashed-{plain}"
        return hasher

    @pytest.fixture
    def service(self, user_repo, session_repo, password_hasher) -> UserService:
        return UserService(
            user_repo=user_repo,
            session_repo=session_repo,
            password_hasher_port=password_hasher,
        )

    async def test_register_user_success(self, service, user_repo, password_hasher):
        user_repo.exists.return_value = False

        await service.register_user("alice", "secret")

        user_repo.save.assert_called_once()
        saved_user = user_repo.save.call_args[1]["user"]
        assert saved_user.username == "alice"
        assert saved_user.hashed_password == "hashed-secret"

    async def test_register_user_already_exists(self, service, user_repo):
        user_repo.exists.return_value = True
        with pytest.raises(UserAlreadyExists):
            await service.register_user("alice", "secret")

    async def test_login_user_success(
        self, service, user_repo, session_repo, password_hasher
    ):
        user = User(username="alice", hashed_password="hashed-secret", id=uuid4())
        user_repo.get_by_username.return_value = user

        session = await service.login_user("alice", "secret")

        assert isinstance(session, UserSession)
        assert session.user_id == user.id
        session_repo.save.assert_awaited_once_with(session=session)

    async def test_login_user_invalid_credentials(self, service, user_repo):
        user_repo.get_by_username.return_value = None
        with pytest.raises(UserInvalidCredentials):
            await service.login_user("alice", "secret")

        user_repo.get_by_username.return_value = User(
            username="alice", hashed_password="hashed-other"
        )
        with pytest.raises(UserInvalidCredentials):
            await service.login_user("alice", "wrong-password")

    async def test_logout_user_success(self, service, session_repo):
        session_id = str(uuid4())

        await service.logout_user(session_id=session_id)

        session_repo.delete_by_id.assert_awaited_once()
        called_uuid = session_repo.delete_by_id.call_args[1]["session_id"]
        assert isinstance(called_uuid, UUID)

    async def test_logout_user_not_found(self, service):
        with pytest.raises(SessionNotFound):
            await service.logout_user(session_id=None)

        with pytest.raises(InvalidSession):
            await service.logout_user(session_id="invalid-uuid")

    async def test_get_user_by_session_success(self, service, user_repo, session_repo):
        user = User(username="alice", hashed_password="hashed-secret", id=uuid4())
        session = UserSession(
            user_id=user.id, connected_at=datetime.now(timezone.utc), id=uuid4()
        )

        session_repo.get.return_value = session
        user_repo.get_by_id.return_value = user

        result = await service.get_user_by_session(str(session.id))
        assert result == user

    async def test_get_user_by_session_not_found(self, service, session_repo):
        session_repo.get.return_value = None
        with pytest.raises(SessionNotFound):
            await service.get_user_by_session(str(uuid4()))

        with pytest.raises(SessionNotFound):
            await service.get_user_by_session(None)

        with pytest.raises(InvalidSession):
            await service.get_user_by_session("invalid-uuid")

    async def test_get_user_by_session_user_not_found(
        self, service, user_repo, session_repo
    ):
        session = UserSession(
            user_id=uuid4(), connected_at=datetime.now(timezone.utc), id=uuid4()
        )
        session_repo.get.return_value = session
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFound):
            await service.get_user_by_session(str(session.id))

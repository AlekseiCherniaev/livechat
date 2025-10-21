from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pytest_asyncio import fixture

from app.domain.dtos.user import UserAuthDTO
from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.user import (
    UserAlreadyExists,
    UserInvalidCredentials,
    UserNotFound,
)
from app.domain.exceptions.user_session import SessionNotFound, InvalidSession
from app.domain.services.user import UserService


class TestUserService:
    @fixture
    def service(
        self,
        user_repo,
        session_repo,
        ws_session_repo,
        outbox_repo,
        password_hasher,
        connection_port,
        cache_port,
        tm,
    ):
        return UserService(
            user_repo=user_repo,
            session_repo=session_repo,
            ws_session_repo=ws_session_repo,
            outbox_repo=outbox_repo,
            password_hasher_port=password_hasher,
            connection_port=connection_port,
            cache_port=cache_port,
            transaction_manager=tm,
        )

    async def test_register_user_success(self, service, user_repo, password_hasher):
        user_data = UserAuthDTO(username="alice", password="secret")
        user_repo.exists.return_value = False
        user_repo.save.return_value = User(
            id=uuid4(), username="alice", hashed_password="hashed-secret"
        )

        await service.register_user(user_data)

        user_repo.exists.assert_awaited_once_with(username="alice")
        user_repo.save.assert_awaited_once()
        password_hasher.hash.assert_called_once_with(password="secret")

    async def test_register_user_already_exists(self, service, user_repo):
        user_repo.exists.return_value = True
        user_data = UserAuthDTO(username="bob", password="123")
        with pytest.raises(UserAlreadyExists):
            await service.register_user(user_data)

    async def test_login_user_success(self, service, user_repo, session_repo):
        user_id = uuid4()
        user = User(id=user_id, username="john", hashed_password="hashed-pass")
        user_repo.get_by_username.return_value = user
        service._password_hasher.verify.return_value = True
        session_repo.save.return_value = UserSession(
            id=uuid4(), user_id=user_id, connected_at=datetime.now(timezone.utc)
        )

        session_id = await service.login_user(
            UserAuthDTO(username="john", password="pass")
        )

        user_repo.get_by_username.assert_awaited_once_with(username="john")
        session_repo.save.assert_awaited_once()
        assert isinstance(session_id, uuid4().__class__)

    async def test_login_user_invalid_username(self, service, user_repo):
        user_repo.get_by_username.return_value = None
        with pytest.raises(UserInvalidCredentials):
            await service.login_user(UserAuthDTO(username="bad", password="pwd"))

    async def test_login_user_invalid_password(self, service, user_repo):
        user = User(id=uuid4(), username="john", hashed_password="hashed-pass")
        user_repo.get_by_username.return_value = user
        service._password_hasher.verify.return_value = False
        with pytest.raises(UserInvalidCredentials):
            await service.login_user(UserAuthDTO(username="john", password="wrong"))

    async def test_logout_user_success(
        self, service, session_repo, user_repo, ws_session_repo
    ):
        user_id = uuid4()
        session_id = uuid4()
        session_repo.get_by_id.return_value = UserSession(
            id=session_id, user_id=user_id, connected_at=datetime.now(timezone.utc)
        )

        await service.logout_user(str(session_id))

        session_repo.get_by_id.assert_awaited_once_with(session_id=session_id)
        user_repo.update_last_active.assert_awaited_once()
        session_repo.delete_by_id.assert_awaited()
        ws_session_repo.delete_by_user_id.assert_awaited()

    async def test_logout_user_no_session(self, service):
        with pytest.raises(SessionNotFound):
            await service.logout_user(None)

    async def test_logout_user_invalid_uuid(self, service):
        with pytest.raises(InvalidSession):
            await service.logout_user("not-a-uuid")

    async def test_logout_user_not_found(self, service, session_repo):
        session_repo.get_by_id.return_value = None
        with pytest.raises(SessionNotFound):
            await service.logout_user(str(uuid4()))

    async def test_get_user_by_session_success(
        self, service, session_repo, user_repo, cache_port
    ):
        user_id = uuid4()
        session_id = uuid4()
        session_repo.get_by_id.return_value = UserSession(
            id=session_id, user_id=user_id, connected_at=datetime.now(timezone.utc)
        )
        user_repo.get_by_id.return_value = User(
            id=user_id, username="alice", hashed_password="x"
        )
        cache_port.get.return_value = None

        result = await service.get_user_by_session(str(session_id))

        session_repo.get_by_id.assert_awaited_once_with(session_id=session_id)
        user_repo.get_by_id.assert_awaited_once_with(user_id=user_id)
        assert result.username == "alice"

    async def test_get_user_by_session_not_found(self, service, session_repo):
        session_repo.get_by_id.return_value = None
        with pytest.raises(SessionNotFound):
            await service.get_user_by_session(str(uuid4()))

    async def test_get_user_by_session_user_not_found(
        self, service, session_repo, user_repo, cache_port
    ):
        session_id = uuid4()
        session_repo.get_by_id.return_value = UserSession(
            id=session_id, user_id=uuid4(), connected_at=datetime.now(timezone.utc)
        )
        user_repo.get_by_id.return_value = None
        cache_port.get.return_value = None

        with pytest.raises(UserNotFound):
            await service.get_user_by_session(str(session_id))

    async def test_get_user_by_session_invalid(self, service):
        with pytest.raises(InvalidSession):
            await service.get_user_by_session("not-uuid")

    async def test_get_user_by_session_none(self, service):
        with pytest.raises(SessionNotFound):
            await service.get_user_by_session(None)

from datetime import datetime, timezone
from uuid import uuid4, UUID

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
        self, user_repo, session_repo, outbox_repo, password_hasher, tm
    ) -> UserService:
        return UserService(
            user_repo=user_repo,
            session_repo=session_repo,
            outbox_repo=outbox_repo,
            password_hasher_port=password_hasher,
            transaction_manager=tm,
        )

    @fixture
    def user_auth_dto(self):
        return UserAuthDTO(username="alice", password="secret")

    async def test_register_user_success(self, service, user_repo, tm, user_auth_dto):
        user_repo.exists.return_value = False
        user_repo.save.side_effect = lambda user: user

        await service.register_user(user_auth_dto)

        user_repo.exists.assert_awaited_once_with(username="alice")
        tm.run_in_transaction.assert_awaited_once()
        user_repo.save.assert_awaited()
        service._outbox_repo.save.assert_awaited_once()

    async def test_register_user_already_exists(
        self, service, user_repo, user_auth_dto
    ):
        user_repo.exists.return_value = True
        with pytest.raises(UserAlreadyExists):
            await service.register_user(user_auth_dto)

    async def test_login_user_success(
        self, service, user_repo, session_repo, password_hasher, tm, user_auth_dto
    ):
        user = User(username="alice", hashed_password="hashed-secret", id=uuid4())
        user_repo.get_by_username.return_value = user
        session_repo.save.side_effect = lambda session: session

        result = await service.login_user(user_auth_dto)

        assert isinstance(result, UUID)
        tm.run_in_transaction.assert_awaited_once()
        session_repo.save.assert_awaited_once()
        service._outbox_repo.save.assert_awaited_once()

    async def test_login_user_invalid_credentials(
        self, service, user_repo, password_hasher, user_auth_dto
    ):
        user_repo.get_by_username.return_value = None
        with pytest.raises(UserInvalidCredentials):
            await service.login_user(user_auth_dto)

        user_repo.get_by_username.return_value = User(
            username="alice", hashed_password="hashed-other"
        )
        with pytest.raises(UserInvalidCredentials):
            await service.login_user(UserAuthDTO(username="alice", password="wrong"))

    async def test_logout_user_success(self, service, session_repo, tm):
        session = UserSession(
            user_id=uuid4(), connected_at=datetime.now(timezone.utc), id=uuid4()
        )
        session_repo.get.return_value = session

        await service.logout_user(session_id=str(session.id))

        session_repo.get.assert_awaited_once_with(session.id)
        session_repo.delete_by_id.assert_awaited_once_with(session_id=session.id)
        tm.run_in_transaction.assert_awaited_once()
        service._outbox_repo.save.assert_awaited_once()

    async def test_logout_user_not_found_or_invalid(self, service):
        with pytest.raises(SessionNotFound):
            await service.logout_user(session_id=None)
        with pytest.raises(InvalidSession):
            await service.logout_user(session_id="invalid-uuid")

    async def test_get_user_by_session_success(self, service, user_repo, session_repo):
        user = User(username="bob", hashed_password="hashed-secret", id=uuid4())
        session = UserSession(
            user_id=user.id, connected_at=datetime.now(timezone.utc), id=uuid4()
        )

        session_repo.get.return_value = session
        user_repo.get_by_id.return_value = user

        result = await service.get_user_by_session(str(session.id))

        assert result.username == user.username
        session_repo.get.assert_awaited_once()
        user_repo.get_by_id.assert_awaited_once_with(user_id=user.id)

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

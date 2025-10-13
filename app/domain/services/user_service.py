from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.session import SessionNotFound, InvalidSession
from app.domain.exceptions.user import (
    UserAlreadyExists,
    UserInvalidCredentials,
    UserNotFound,
)
from app.domain.ports.password_hasher import PasswordHasherPort
from app.domain.repos.session import SessionRepository
from app.domain.repos.user import UserRepository

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        password_hasher_port: PasswordHasherPort,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._password_hasher = password_hasher_port

    async def register_user(self, username: str, password: str) -> None:
        if await self._user_repo.exists(username=username):
            raise UserAlreadyExists

        hashed_password = self._password_hasher.hash(password=password)
        user = User(username=username, hashed_password=hashed_password)

        await self._user_repo.save(user=user)
        logger.bind(username=user.username).debug("Saved user in repo")

    async def login_user(self, username: str, password: str) -> UserSession:
        user = await self._user_repo.get_by_username(username=username)
        if not user or not self._password_hasher.verify(password, user.hashed_password):
            raise UserInvalidCredentials

        session = UserSession(user_id=user.id, connected_at=datetime.now(timezone.utc))
        await self._session_repo.save(session=session)
        logger.bind(session_id=session.id).debug("Saved session in repo")
        return session

    async def logout_user(self, session_id: str | None) -> None:
        if not session_id:
            raise SessionNotFound

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise InvalidSession

        await self._session_repo.delete_by_id(session_id=session_uuid)
        logger.bind(session_id=session_uuid).debug("Deleted session in repo")

    async def get_user_by_session(self, session_id: str | None) -> User:
        if not session_id:
            raise SessionNotFound

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise InvalidSession

        session = await self._session_repo.get(session_id=session_uuid)
        if not session:
            raise SessionNotFound

        user = await self._user_repo.get_by_id(user_id=session.user_id)
        if not user:
            raise UserNotFound
        logger.bind(user_id=user.id).debug("Retrieved user from repo")
        return user

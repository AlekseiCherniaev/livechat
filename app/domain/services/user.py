from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.domain.dtos.user import UserAuthDTO, UserPublicDTO
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

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: UserSessionRepository,
        password_hasher_port: PasswordHasherPort,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._password_hasher = password_hasher_port

    @staticmethod
    def _user_to_dto(user: User) -> UserPublicDTO:
        return UserPublicDTO(
            username=user.username,
            last_active_at=user.last_active_at,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            id=user.id,
        )

    async def register_user(self, user_data: UserAuthDTO) -> None:
        if await self._user_repo.exists(username=user_data.username):
            raise UserAlreadyExists

        hashed_password = self._password_hasher.hash(password=user_data.password)
        user = User(username=user_data.username, hashed_password=hashed_password)

        await self._user_repo.save(user=user)
        logger.bind(username=user.username).debug("Saved user in repo")

    async def login_user(self, user_data: UserAuthDTO) -> UserSession:
        user = await self._user_repo.get_by_username(username=user_data.username)
        if not user or not self._password_hasher.verify(
            user_data.password, user.hashed_password
        ):
            raise UserInvalidCredentials

        user.last_login_at = datetime.now(timezone.utc)
        await self._user_repo.save(user)

        session = UserSession(user_id=user.id, connected_at=datetime.now(timezone.utc))
        await self._session_repo.save(session=session)
        logger.bind(session_id=session.id).debug(
            "Saved session and updated user in repo"
        )
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

    async def get_user_by_session(self, session_id: str | None) -> UserPublicDTO:
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
        return self._user_to_dto(user=user)

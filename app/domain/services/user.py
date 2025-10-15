from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.core.constants import AnalyticsEventType, OutboxMessageType, OutboxStatus
from app.domain.dtos.user import UserAuthDTO, UserPublicDTO
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.outbox_event import OutboxEvent
from app.domain.entities.user import User
from app.domain.entities.user_session import UserSession
from app.domain.exceptions.user_session import SessionNotFound, InvalidSession
from app.domain.exceptions.user import (
    UserAlreadyExists,
    UserInvalidCredentials,
    UserNotFound,
)
from app.domain.ports.password_hasher import PasswordHasherPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.outbox_event import OutboxEventRepository
from app.domain.repos.user_session import UserSessionRepository
from app.domain.repos.user import UserRepository

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: UserSessionRepository,
        outbox_repo: OutboxEventRepository,
        password_hasher_port: PasswordHasherPort,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._outbox_repo = outbox_repo
        self._password_hasher = password_hasher_port
        self._tm = transaction_manager

    @staticmethod
    def _user_to_dto(user: User) -> UserPublicDTO:
        return UserPublicDTO(
            username=user.username,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            id=user.id,
        )

    async def register_user(self, user_data: UserAuthDTO) -> None:
        if await self._user_repo.exists(username=user_data.username):
            raise UserAlreadyExists

        async def _txn():
            hashed_password = self._password_hasher.hash(password=user_data.password)
            user = User(username=user_data.username, hashed_password=hashed_password)
            user = await self._user_repo.save(user=user)

            event = AnalyticsEvent(
                event_type=AnalyticsEventType.USER_REGISTERED,
                user_id=user.id,
            )
            outbox = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"user_register:{user.id}",
            )
            await self._outbox_repo.save(outbox)

            return user

        user_create = await self._tm.run_in_transaction(_txn)

        await self._user_repo.save(user=user_create)
        logger.bind(username=user_create.username).debug("Saved user in repo")

    async def login_user(self, user_data: UserAuthDTO) -> UserSession:
        user = await self._user_repo.get_by_username(username=user_data.username)
        if not user or not self._password_hasher.verify(
            user_data.password, user.hashed_password
        ):
            raise UserInvalidCredentials

        async def _txn():
            user.last_login_at = datetime.now(timezone.utc)
            await self._user_repo.save(user)

            session = UserSession(
                user_id=user.id, connected_at=datetime.now(timezone.utc)
            )
            await self._session_repo.save(session=session)

            event = AnalyticsEvent(
                event_type=AnalyticsEventType.USER_LOGGED_IN,
                user_id=user.id,
            )
            outbox = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"user_login:{user.id}:{session.connected_at.timestamp()}",
            )
            await self._outbox_repo.save(outbox)

            return session

        session_create = await self._tm.run_in_transaction(_txn)
        logger.bind(session_id=session_create.id).debug(
            "Saved session and updated user in repo"
        )

        return session_create

    async def logout_user(self, session_id: str | None) -> None:
        if not session_id:
            raise SessionNotFound

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise InvalidSession

        session = await self._session_repo.get(session_uuid)
        if not session:
            raise SessionNotFound

        async def _txn():
            await self._session_repo.delete_by_id(session_id=session_uuid)

            event = AnalyticsEvent(
                event_type=AnalyticsEventType.USER_LOGGED_OUT,
                user_id=session.user_id,
            )
            outbox = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"user_logout:{session.user_id}:{session.id}",
            )
            await self._outbox_repo.save(outbox)

        await self._tm.run_in_transaction(_txn)
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

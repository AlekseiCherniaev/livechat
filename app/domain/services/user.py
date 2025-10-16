from datetime import datetime, timezone
from uuid import UUID
from typing import Any
import structlog

from app.core.constants import AnalyticsEventType
from app.domain.dtos.user import UserAuthDTO, UserPublicDTO, user_to_dto
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
from app.domain.repos.notification import NotificationRepository
from app.domain.repos.outbox import OutboxRepository
from app.domain.repos.user_session import UserSessionRepository
from app.domain.repos.user import UserRepository
from app.domain.repos.websocket_session import WebSocketSessionRepository
from app.domain.services.utils import create_outbox_analytics_event

logger = structlog.get_logger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: UserSessionRepository,
        ws_session_repo: WebSocketSessionRepository,
        notif_repo: NotificationRepository,
        outbox_repo: OutboxRepository,
        password_hasher_port: PasswordHasherPort,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._ws_session_repo = ws_session_repo
        self._notif_repo = notif_repo
        self._outbox_repo = outbox_repo
        self._password_hasher = password_hasher_port
        self._tm = transaction_manager

    async def register_user(self, user_data: UserAuthDTO) -> None:
        if await self._user_repo.exists(username=user_data.username):
            raise UserAlreadyExists

        async def _txn(db_session: Any):
            hashed_password = self._password_hasher.hash(password=user_data.password)
            user = User(username=user_data.username, hashed_password=hashed_password)
            user = await self._user_repo.save(user=user, db_session=db_session)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_REGISTERED,
                user_id=user.id,
                dedup_key=f"user_register:{user.id}",
                db_session=db_session,
            )

            logger.bind(username=user.username).debug("Saved user in repo")

        await self._tm.run_in_transaction(_txn)

    async def login_user(self, user_data: UserAuthDTO) -> UUID:
        user = await self._user_repo.get_by_username(username=user_data.username)
        if not user or not self._password_hasher.verify(
            user_data.password, user.hashed_password
        ):
            raise UserInvalidCredentials

        async def _txn(db_session: Any):
            user.last_login_at = datetime.now(timezone.utc)
            user.last_active = datetime.now(timezone.utc)
            await self._user_repo.save(user=user, db_session=db_session)

            session = UserSession(
                user_id=user.id, connected_at=datetime.now(timezone.utc)
            )

            await self._session_repo.save(session=session, db_session=db_session)
            # in case Mongo commit fails after this step, a session may remain in Redis,
            # but it will expire automatically (TTL) and is never returned to the user

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_LOGGED_IN,
                user_id=user.id,
                dedup_key=f"user_login:{user.id}:{session.connected_at.timestamp()}",
                db_session=db_session,
            )

            logger.bind(session_id=session.id).debug(
                "Saved session and updated user in repo"
            )

            return session.id

        session_id = await self._tm.run_in_transaction(_txn)

        return session_id

    async def logout_user(self, session_id: str | None) -> None:
        if not session_id:
            raise SessionNotFound

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise InvalidSession

        session = await self._session_repo.get_by_id(session_id=session_uuid)
        if not session:
            raise SessionNotFound

        async def _txn(db_session: Any):
            await self._user_repo.update_last_active(
                session.user_id, db_session=db_session
            )
            await self._session_repo.delete_by_id(
                session_id=session_uuid, db_session=db_session
            )
            await self._ws_session_repo.delete_by_user_id(
                user_id=session.user_id, db_session=db_session
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_LOGGED_OUT,
                user_id=session.user_id,
                dedup_key=f"user_logout:{session.user_id}:{session.id}",
                db_session=db_session,
            )

            logger.bind(session_id=session_uuid).debug("Deleted session in repo")

        await self._tm.run_in_transaction(_txn)

    async def delete_user(self, user_id: UUID) -> None:
        async def _txn(db_session: Any):
            await self._notif_repo.delete_by_user_id(
                user_id=user_id, db_session=db_session
            )
            await self._user_repo.delete_by_id(user_id=user_id, db_session=db_session)
            await self._session_repo.delete_by_user_id(
                user_id=user_id, db_session=db_session
            )
            await self._ws_session_repo.delete_by_user_id(
                user_id=user_id, db_session=db_session
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.USER_DELETED,
                user_id=user_id,
                dedup_key=f"user_delete:{user_id}",
                db_session=db_session,
            )

            logger.bind(session_id=user_id).debug("Deleted user in repo")

        await self._tm.run_in_transaction(_txn)

    async def get_user_by_session(self, session_id: str | None) -> UserPublicDTO:
        if not session_id:
            raise SessionNotFound

        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise InvalidSession

        session = await self._session_repo.get_by_id(session_id=session_uuid)
        if not session:
            raise SessionNotFound

        user = await self._user_repo.get_by_id(user_id=session.user_id)
        if not user:
            raise UserNotFound

        logger.bind(user_id=user.id).debug("Retrieved user from repo")
        return user_to_dto(user=user)

from clickhouse_connect.driver.asyncclient import AsyncClient
from fastapi import Request, Depends

from app.adapters.db.repos.chat_room import MongoChatRoomRepository
from app.adapters.db.repos.message_repo import CassandraMessageRepository
from app.adapters.db.repos.notification import MongoNotificationRepository
from app.adapters.db.repos.user_session import RedisSessionRepository
from app.adapters.db.repos.user import MongoUserRepository
from app.domain.ports.password_hasher import PasswordHasherPort
from app.domain.repos.chat_room import ChatRoomRepository
from app.domain.repos.message import MessageRepository
from app.domain.repos.notification import NotificationRepository
from app.domain.repos.user_session import UserSessionRepository
from app.domain.repos.user import UserRepository
from app.domain.services.user_service import UserService


def get_bcrypt_password_hasher(request: Request) -> PasswordHasherPort:
    return request.app.state.bcrypt_password_hasher  # type: ignore


def get_clickhouse_client(request: Request) -> AsyncClient:
    return request.app.state.clickhouse  # type: ignore


def get_user_repo(request: Request) -> UserRepository:
    return MongoUserRepository(db=request.app.state.mongo_db)


def get_session_repo(request: Request) -> UserSessionRepository:
    return RedisSessionRepository(redis=request.app.state.redis)


def get_notification_repo(request: Request) -> NotificationRepository:
    return MongoNotificationRepository(db=request.app.state.mongo_db)


def get_chat_repo(request: Request) -> ChatRoomRepository:
    return MongoChatRoomRepository(db=request.app.state.mongo_db)


def get_message_repo() -> MessageRepository:
    return CassandraMessageRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: UserSessionRepository = Depends(get_session_repo),
    password_hasher: PasswordHasherPort = Depends(get_bcrypt_password_hasher),
) -> UserService:
    return UserService(
        user_repo=user_repo,
        session_repo=session_repo,
        password_hasher_port=password_hasher,
    )

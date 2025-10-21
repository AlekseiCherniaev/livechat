from typing import Any

from clickhouse_connect.driver.asyncclient import AsyncClient
from fastapi import Request, Depends
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from redis.asyncio import Redis
from starlette.websockets import WebSocket

from app.adapters.analytics.analytics import ClickHouseAnalyticsRepository
from app.adapters.cache.memcache import MemcachedCache
from app.adapters.connection.redis_connection import RedisConnectionPort
from app.adapters.db.cassandra_engine import CassandraEngine
from app.adapters.db.mongo_trans_manager import MongoTransactionManager
from app.adapters.db.repos.cassandra.message import CassandraMessageRepository
from app.adapters.db.repos.mongo.join_request import MongoJoinRequestRepository
from app.adapters.db.repos.mongo.notification import MongoNotificationRepository
from app.adapters.db.repos.mongo.outbox import MongoOutboxRepository
from app.adapters.db.repos.mongo.room import MongoRoomRepository
from app.adapters.db.repos.mongo.room_membership import MongoRoomMembershipRepository
from app.adapters.db.repos.mongo.user import MongoUserRepository
from app.adapters.db.repos.redis.user_session import RedisSessionRepository
from app.adapters.db.repos.redis.websocket_session import (
    RedisWebSocketSessionRepository,
)
from app.adapters.notification_sender.websocket_sender import (
    WebSocketNotificationSender,
)
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
from app.domain.services.analytics import AnalyticsService
from app.domain.services.message import MessageService
from app.domain.services.notification import NotificationService
from app.domain.services.room import RoomService
from app.domain.services.user import UserService
from app.domain.services.websocket import WebSocketService


def get_mongo_client(request: Request) -> AsyncMongoClient[Any]:
    return request.app.state.mongo_client  # type: ignore


def get_mongo_db(request: Request) -> AsyncDatabase[Any]:
    return request.app.state.mongo_db  # type: ignore


def get_redis(request: Request) -> Redis:
    return request.app.state.redis  # type: ignore


def get_memcache(request: Request) -> MemcachedCache:
    return request.app.state.memcache  # type: ignore


def get_cassandra_engine(request: Request) -> CassandraEngine:
    return request.app.state.cassandra_engine  # type: ignore


def get_clickhouse(request: Request) -> AsyncClient:
    return request.app.state.clickhouse  # type: ignore


def get_analytics(
    client: AsyncClient = Depends(get_clickhouse),
) -> AnalyticsPort:
    return ClickHouseAnalyticsRepository(client=client)


def get_connection(
    redis: Redis = Depends(get_redis),
) -> ConnectionPort:
    return RedisConnectionPort(redis=redis)


def get_notification_sender(
    connection_port: ConnectionPort = Depends(get_connection),
) -> NotificationSenderPort:
    return WebSocketNotificationSender(connection_port=connection_port)


def get_password_hasher(request: Request) -> PasswordHasherPort:
    return request.app.state.bcrypt_password_hasher  # type: ignore


def get_transaction_manager(
    client: AsyncMongoClient[Any] = Depends(get_mongo_client),
) -> TransactionManager:
    return MongoTransactionManager(client=client)


def get_join_request_repo(
    db: AsyncDatabase[Any] = Depends(get_mongo_db),
) -> JoinRequestRepository:
    return MongoJoinRequestRepository(db=db)


def get_message_repo() -> MessageRepository:
    return CassandraMessageRepository()


def get_notification_repo(
    db: AsyncDatabase[Any] = Depends(get_mongo_db),
) -> NotificationRepository:
    return MongoNotificationRepository(db=db)


def get_outbox_repo(db: AsyncDatabase[Any] = Depends(get_mongo_db)) -> OutboxRepository:
    return MongoOutboxRepository(db=db)


def get_room_repo(db: AsyncDatabase[Any] = Depends(get_mongo_db)) -> RoomRepository:
    return MongoRoomRepository(db=db)


def get_room_membership_repo(
    db: AsyncDatabase[Any] = Depends(get_mongo_db),
) -> RoomMembershipRepository:
    return MongoRoomMembershipRepository(db=db)


def get_user_repo(db: AsyncDatabase[Any] = Depends(get_mongo_db)) -> UserRepository:
    return MongoUserRepository(db=db)


def get_user_session_repo(redis: Redis = Depends(get_redis)) -> UserSessionRepository:
    return RedisSessionRepository(redis=redis)


def get_websocket_session_repo(
    redis: Redis = Depends(get_redis),
) -> WebSocketSessionRepository:
    return RedisWebSocketSessionRepository(redis=redis)


def get_message_service(
    message_repo: MessageRepository = Depends(get_message_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    membership_repo: RoomMembershipRepository = Depends(get_room_membership_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
    connection_port: ConnectionPort = Depends(get_connection),
    transaction_manager: TransactionManager = Depends(get_transaction_manager),
) -> MessageService:
    return MessageService(
        message_repo=message_repo,
        user_repo=user_repo,
        membership_repo=membership_repo,
        outbox_repo=outbox_repo,
        connection_port=connection_port,
        transaction_manager=transaction_manager,
    )


def get_notification_service(
    notification_repo: NotificationRepository = Depends(get_notification_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
    transaction_manager: TransactionManager = Depends(get_transaction_manager),
) -> NotificationService:
    return NotificationService(
        notification_repo=notification_repo,
        outbox_repo=outbox_repo,
        transaction_manager=transaction_manager,
    )


def get_room_service(
    room_repo: RoomRepository = Depends(get_room_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    join_request_repo: JoinRequestRepository = Depends(get_join_request_repo),
    room_membership_repo: RoomMembershipRepository = Depends(get_room_membership_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
    connection_port: ConnectionPort = Depends(get_connection),
    transaction_manager: TransactionManager = Depends(get_transaction_manager),
) -> RoomService:
    return RoomService(
        room_repo=room_repo,
        user_repo=user_repo,
        join_request_repo=join_request_repo,
        room_membership_repo=room_membership_repo,
        outbox_repo=outbox_repo,
        connection_port=connection_port,
        transaction_manager=transaction_manager,
    )


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
    ws_session_repo: WebSocketSessionRepository = Depends(get_websocket_session_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
    password_hasher: PasswordHasherPort = Depends(get_password_hasher),
    connection_port: ConnectionPort = Depends(get_connection),
    cache_port: CachePort = Depends(get_memcache),
    transaction_manager: TransactionManager = Depends(get_transaction_manager),
) -> UserService:
    return UserService(
        user_repo=user_repo,
        session_repo=session_repo,
        ws_session_repo=ws_session_repo,
        outbox_repo=outbox_repo,
        password_hasher_port=password_hasher,
        connection_port=connection_port,
        cache_port=cache_port,
        transaction_manager=transaction_manager,
    )


def get_websocket_service(
    ws_session_repo: WebSocketSessionRepository = Depends(get_websocket_session_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
    room_repo: RoomRepository = Depends(get_room_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
    membership_repo: RoomMembershipRepository = Depends(get_room_membership_repo),
    connection_port: ConnectionPort = Depends(get_connection),
    transaction_manager: TransactionManager = Depends(get_transaction_manager),
) -> WebSocketService:
    return WebSocketService(
        ws_session_repo=ws_session_repo,
        user_repo=user_repo,
        session_repo=session_repo,
        room_repo=room_repo,
        outbox_repo=outbox_repo,
        membership_repo=membership_repo,
        connection_port=connection_port,
        transaction_manager=transaction_manager,
    )


def get_websocket_service_from_websocket(
    websocket: WebSocket,
) -> WebSocketService:
    mongo_db = websocket.app.state.mongo_db
    mongo_client = websocket.app.state.mongo_client
    redis = websocket.app.state.redis

    return WebSocketService(
        ws_session_repo=RedisWebSocketSessionRepository(redis=redis),
        user_repo=MongoUserRepository(db=mongo_db),
        session_repo=RedisSessionRepository(redis=redis),
        room_repo=MongoRoomRepository(db=mongo_db),
        outbox_repo=MongoOutboxRepository(db=mongo_db),
        membership_repo=MongoRoomMembershipRepository(db=mongo_db),
        connection_port=RedisConnectionPort(redis=redis),
        transaction_manager=MongoTransactionManager(client=mongo_client),
    )


def get_analytics_service(
    analytics_port: AnalyticsPort = Depends(get_analytics),
) -> AnalyticsService:
    return AnalyticsService(analytics_port=analytics_port)

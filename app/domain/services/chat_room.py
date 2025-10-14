from datetime import timezone, datetime
from uuid import UUID

import structlog

from app.core.constants import (
    JoinRequestStatus,
    NotificationType,
    AnalyticsEventType,
    RoomRole,
)
from app.domain.dtos.chat_room import (
    ChatRoomCreateDTO,
    ChatRoomPublicDTO,
    ChatRoomUpdateDTO,
)
from app.domain.dtos.join_request import JoinRequestCreateDTO
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.chat_room import ChatRoom
from app.domain.entities.join_request import JoinRequest
from app.domain.entities.notification import Notification
from app.domain.entities.room_membership import RoomMembership
from app.domain.exceptions.chat_room import (
    ChatRoomAlreadyExists,
    ChatRoomNotFound,
    NoChangesDetected,
)
from app.domain.exceptions.join_request import (
    JoinRequestNotFound,
    JoinRequestAlreadyExists,
)
from app.domain.exceptions.user import UserNotFound
from app.domain.ports.analytics import AnalyticsPort
from app.domain.ports.notification_sender import NotificationSenderPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.chat_room import ChatRoomRepository
from app.domain.repos.join_request import JoinRequestRepository
from app.domain.repos.room_membership import RoomMembershipRepository
from app.domain.repos.user import UserRepository

logger = structlog.get_logger(__name__)


class ChatRoomService:
    def __init__(
        self,
        room_repo: ChatRoomRepository,
        user_repo: UserRepository,
        join_repo: JoinRequestRepository,
        membership_repo: RoomMembershipRepository,
        analytics_port: AnalyticsPort,
        notification_port: NotificationSenderPort,
        transaction_manager: TransactionManager,
    ):
        self._room_repo = room_repo
        self._user_repo = user_repo
        self._join_repo = join_repo
        self._membership_repo = membership_repo
        self._analytics = analytics_port
        self._notifier = notification_port
        self._tm = transaction_manager

    @staticmethod
    def _room_to_dto(room: ChatRoom) -> ChatRoomPublicDTO:
        return ChatRoomPublicDTO(
            name=room.name,
            description=room.description,
            is_public=room.is_public,
            created_by=room.created_by,
            participants_count=room.participants_count,
            created_at=room.created_at,
            updated_at=room.updated_at,
            id=room.id,
        )

    async def create_room(self, room_data: ChatRoomCreateDTO) -> ChatRoomPublicDTO:
        if await self._room_repo.exists(name=room_data.name):
            raise ChatRoomAlreadyExists

        if not await self._user_repo.get_by_id(room_data.created_by):
            raise UserNotFound

        async def _txn():
            _room = ChatRoom(
                name=room_data.name,
                description=room_data.description,
                is_public=room_data.is_public,
                created_by=room_data.created_by,
                participants_count=0,
            )
            _room = await self._room_repo.save(room=_room)
            await self._add_participant(_room.id, room_data.created_by, RoomRole.OWNER)
            return _room

        room = await self._tm.run_in_transaction(_txn)
        logger.bind(room_id=room.id).info("Room created")

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=AnalyticsEventType.ROOM_CREATED,
                user_id=room_data.created_by,
                room_id=room.id,
            )
        )

        return self._room_to_dto(room=room)

    async def update_room(
        self, room_id: UUID, room_data: ChatRoomUpdateDTO
    ) -> ChatRoomPublicDTO:
        room = await self._room_repo.get(room_id=room_id)
        if not room:
            raise ChatRoomNotFound

        changed = False
        if (
            room_data.description is not None
            and room.description != room_data.description
        ):
            room.description = room_data.description
            changed = True
        if room_data.is_public is not None and room.is_public != room_data.is_public:
            room.is_public = room_data.is_public
            changed = True
        if not changed:
            raise NoChangesDetected

        room.updated_at = datetime.now(timezone.utc)
        await self._room_repo.update(room=room)
        logger.bind(room_id=room.id).info("Room updated")

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=AnalyticsEventType.ROOM_UPDATED,
                user_id=room.created_by,
                room_id=room.id,
            )
        )

        return self._room_to_dto(room=room)

    async def delete_room(self, room_id: UUID) -> None:
        room = await self._room_repo.get(room_id=room_id)
        if not room:
            raise ChatRoomNotFound

        await self._room_repo.delete_by_id(room_id=room_id)
        logger.bind(room_id=room_id).info("Room deleted")

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=AnalyticsEventType.ROOM_DELETED,
                user_id=room.created_by,
                room_id=room_id,
            )
        )

        return None

    async def get_room(self, room_id: UUID) -> ChatRoomPublicDTO:
        room = await self._room_repo.get(room_id=room_id)
        if room is None:
            raise ChatRoomNotFound
        return self._room_to_dto(room=room)

    async def list_rooms_for_user(self, user_id: UUID) -> list[ChatRoomPublicDTO]:
        rooms = await self._room_repo.list_by_user(user_id=user_id)
        return [self._room_to_dto(room=room) for room in rooms]

    async def list_top_public_rooms(self, limit: int) -> list[ChatRoomPublicDTO]:
        rooms = await self._room_repo.list_top_room(limit=limit, only_public=True)
        return [self._room_to_dto(room) for room in rooms]

    async def list_join_requests(self, room_id: UUID) -> list[JoinRequest]:
        return await self._join_repo.list_by_room(room_id)

    async def search_rooms(self, query: str, limit: int) -> list[ChatRoomPublicDTO]:
        rooms = await self._room_repo.search(query=query, limit=limit)
        return [self._room_to_dto(room=room) for room in rooms]

    async def request_join(self, join_request_data: JoinRequestCreateDTO) -> None:
        room = await self._room_repo.get(room_id=join_request_data.room_id)
        if not room:
            raise ChatRoomNotFound

        user = await self._user_repo.get_by_id(user_id=join_request_data.user_id)
        if user is None:
            raise UserNotFound

        if room.is_public:

            async def _txn():
                await self._add_participant(room.id, join_request_data.user_id)

            await self._tm.run_in_transaction(_txn)
            logger.bind(room_id=room.id, user_id=join_request_data.user_id).info(
                "User joined public room"
            )

            await self._analytics.publish_event(
                AnalyticsEvent(
                    event_type=AnalyticsEventType.USER_JOINED_ROOM,
                    user_id=join_request_data.user_id,
                    room_id=room.id,
                )
            )

            return None

        already_requested = await self._join_repo.exists(
            room_id=room.id, user_id=join_request_data.user_id
        )
        if already_requested:
            raise JoinRequestAlreadyExists

        request = JoinRequest(
            room_id=join_request_data.room_id,
            user_id=join_request_data.user_id,
            status=JoinRequestStatus.PENDING,
            message=join_request_data.message,
        )
        await self._join_repo.save(request=request)
        logger.bind(
            room_id=join_request_data.room_id, user_id=join_request_data.user_id
        ).info("Join request created")

        await self._notifier.send(
            Notification(
                user_id=room.created_by,
                type=NotificationType.JOIN_REQUEST_CREATED,
                payload={
                    "room_name": room.name,
                    "username": user.username,
                },
                source_id=join_request_data.user_id,
            )
        )

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=AnalyticsEventType.JOIN_REQUEST_CREATED,
                user_id=join_request_data.user_id,
                room_id=room.id,
            )
        )

        return None

    async def handle_join_request(self, request_id: UUID, accept: bool) -> None:
        request = await self._join_repo.get(request_id)
        if not request:
            raise JoinRequestNotFound

        room = await self._room_repo.get(room_id=request.room_id)
        if room is None:
            raise ChatRoomNotFound

        async def _txn():
            if accept:
                await self._add_participant(request.room_id, request.user_id)
                request.status = JoinRequestStatus.ACCEPTED
                _notif_type = NotificationType.JOIN_REQUEST_ACCEPTED
                _event_type = AnalyticsEventType.JOIN_REQUEST_ACCEPTED
            else:
                request.status = JoinRequestStatus.REJECTED
                _notif_type = NotificationType.JOIN_REQUEST_REJECTED
                _event_type = AnalyticsEventType.JOIN_REQUEST_ACCEPTED

            request.updated_at = datetime.now(timezone.utc)
            request.handled_by = room.created_by
            await self._join_repo.update(request)
            return _notif_type, _event_type

        notif_type, event_type = await self._tm.run_in_transaction(_txn)
        logger.bind(request_id=request_id, status=request.status).info(
            "Join request handled"
        )

        await self._notifier.send(
            Notification(
                user_id=request.user_id,
                type=notif_type,
                payload={"room_name": room.name},
                source_id=room.created_by,
            )
        )

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=event_type,
                user_id=request.user_id,
                room_id=request.room_id,
            )
        )

        return None

    async def _add_participant(
        self, room_id: UUID, user_id: UUID, role: RoomRole = RoomRole.MEMBER
    ) -> None:
        exists = await self._membership_repo.exists(room_id=room_id, user_id=user_id)
        if exists:
            return None

        room_membership = RoomMembership(
            room_id=room_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.now(timezone.utc),
            last_active_at=datetime.now(timezone.utc),
        )
        await self._membership_repo.save(room_membership=room_membership)
        await self._room_repo.add_participant(room_id=room_id, user_id=user_id)
        logger.bind(room_id=room_id, user_id=user_id).info("User added to room")

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=AnalyticsEventType.USER_JOINED_ROOM,
                user_id=user_id,
                room_id=room_id,
            )
        )

        return None

    async def remove_participant(self, room_id: UUID, user_id: UUID) -> None:
        async def _txn():
            await self._membership_repo.delete(room_id=room_id, user_id=user_id)
            await self._room_repo.remove_participant(room_id, user_id)

        await self._tm.run_in_transaction(_txn)
        logger.bind(room_id=room_id, user_id=user_id).info("User removed from room")

        await self._analytics.publish_event(
            AnalyticsEvent(
                event_type=AnalyticsEventType.USER_LEFT_ROOM,
                user_id=user_id,
                room_id=room_id,
            )
        )

        return None

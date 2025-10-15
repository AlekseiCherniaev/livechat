from datetime import timezone, datetime
from uuid import UUID

import structlog

from app.core.constants import (
    JoinRequestStatus,
    NotificationType,
    AnalyticsEventType,
    RoomRole,
    OutboxMessageType,
    OutboxStatus,
)
from app.domain.dtos.join_request import JoinRequestCreateDTO
from app.domain.dtos.room import (
    RoomCreateDTO,
    RoomPublicDTO,
    RoomUpdateDTO,
)
from app.domain.entities.analytics_event import AnalyticsEvent
from app.domain.entities.join_request import JoinRequest
from app.domain.entities.notification import Notification
from app.domain.entities.outbox_event import OutboxEvent
from app.domain.entities.room import Room
from app.domain.entities.room_membership import RoomMembership
from app.domain.exceptions.join_request import (
    JoinRequestNotFound,
    JoinRequestAlreadyExists,
)
from app.domain.exceptions.room import (
    RoomAlreadyExists,
    RoomNotFound,
    NoChangesDetected,
)
from app.domain.exceptions.user import UserNotFound
from app.domain.ports.analytics import AnalyticsPort
from app.domain.ports.notification_sender import NotificationSenderPort
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.join_request import JoinRequestRepository
from app.domain.repos.outbox_event import OutboxEventRepository
from app.domain.repos.room import RoomRepository
from app.domain.repos.room_membership import RoomMembershipRepository
from app.domain.repos.user import UserRepository

logger = structlog.get_logger(__name__)


class RoomService:
    def __init__(
        self,
        room_repo: RoomRepository,
        user_repo: UserRepository,
        join_repo: JoinRequestRepository,
        membership_repo: RoomMembershipRepository,
        outbox_repo: OutboxEventRepository,
        analytics_port: AnalyticsPort,
        notification_port: NotificationSenderPort,
        transaction_manager: TransactionManager,
    ):
        self._room_repo = room_repo
        self._user_repo = user_repo
        self._join_repo = join_repo
        self._membership_repo = membership_repo
        self._outbox_repo = outbox_repo
        self._analytics = analytics_port
        self._notifier = notification_port
        self._tm = transaction_manager

    @staticmethod
    def _room_to_dto(room: Room) -> RoomPublicDTO:
        return RoomPublicDTO(
            name=room.name,
            description=room.description,
            is_public=room.is_public,
            created_by=room.created_by,
            participants_count=room.participants_count,
            created_at=room.created_at,
            updated_at=room.updated_at,
            id=room.id,
        )

    async def create_room(self, room_data: RoomCreateDTO) -> RoomPublicDTO:
        if await self._room_repo.exists(name=room_data.name):
            raise RoomAlreadyExists

        if not await self._user_repo.get_by_id(room_data.created_by):
            raise UserNotFound

        async def _txn():
            room = Room(
                name=room_data.name,
                description=room_data.description,
                is_public=room_data.is_public,
                created_by=room_data.created_by,
                participants_count=0,
            )
            room = await self._room_repo.save(room=room)
            await self._add_participant(room.id, room_data.created_by, RoomRole.OWNER)

            event = AnalyticsEvent(
                event_type=AnalyticsEventType.ROOM_CREATED,
                user_id=room_data.created_by,
                room_id=room.id,
                payload={"room_name": room.name},
            )
            outbox = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"room_created:{room.id}",
            )
            await self._outbox_repo.save(outbox)

            return room

        room_create = await self._tm.run_in_transaction(_txn)
        logger.bind(room_id=room_create.id).info("Room created")

        return self._room_to_dto(room=room_create)

    async def update_room(
        self, room_id: UUID, room_data: RoomUpdateDTO
    ) -> RoomPublicDTO:
        room = await self._room_repo.get(room_id=room_id)
        if not room:
            raise RoomNotFound

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

        async def _txn():
            room.updated_at = datetime.now(timezone.utc)
            await self._room_repo.update(room)

            event = AnalyticsEvent(
                event_type=AnalyticsEventType.ROOM_UPDATED,
                user_id=room.created_by,
                room_id=room.id,
                payload={"room_name": room.name},
            )
            out_event = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"room_update:{room.id}:{room.updated_at.timestamp()}",
            )
            await self._outbox_repo.save(out_event)

            return room

        room_update = await self._tm.run_in_transaction(_txn)
        logger.bind(room_id=room_update.id).info("Room updated")

        return self._room_to_dto(room=room_update)

    async def delete_room(self, room_id: UUID) -> None:
        room = await self._room_repo.get(room_id=room_id)
        if not room:
            raise RoomNotFound

        async def _txn():
            await self._room_repo.delete_by_id(room_id)
            event = AnalyticsEvent(
                event_type=AnalyticsEventType.ROOM_DELETED,
                user_id=room.created_by,
                room_id=room.id,
                payload={"room_name": room.name},
            )
            out_event = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"room_deleted:{room.id}",
            )
            await self._outbox_repo.save(out_event)

        await self._tm.run_in_transaction(_txn)
        logger.bind(room_id=room_id).info("Room deleted")

    async def get_room(self, room_id: UUID) -> RoomPublicDTO:
        room = await self._room_repo.get(room_id=room_id)
        if room is None:
            raise RoomNotFound
        return self._room_to_dto(room=room)

    async def list_rooms_for_user(self, user_id: UUID) -> list[RoomPublicDTO]:
        rooms = await self._room_repo.list_by_user(user_id=user_id)
        return [self._room_to_dto(room=room) for room in rooms]

    async def list_top_public_rooms(self, limit: int) -> list[RoomPublicDTO]:
        rooms = await self._room_repo.list_top_room(limit=limit, only_public=True)
        return [self._room_to_dto(room) for room in rooms]

    async def list_join_requests(self, room_id: UUID) -> list[JoinRequest]:
        return await self._join_repo.list_by_room(room_id)

    async def search_rooms(self, query: str, limit: int) -> list[RoomPublicDTO]:
        rooms = await self._room_repo.search(query=query, limit=limit)
        return [self._room_to_dto(room=room) for room in rooms]

    async def request_join(self, join_request_data: JoinRequestCreateDTO) -> None:
        room = await self._room_repo.get(room_id=join_request_data.room_id)
        if not room:
            raise RoomNotFound

        user = await self._user_repo.get_by_id(user_id=join_request_data.user_id)
        if user is None:
            raise UserNotFound

        if room.is_public:

            async def _txn():
                await self._add_participant(room.id, join_request_data.user_id)

                event = AnalyticsEvent(
                    event_type=AnalyticsEventType.USER_JOINED_ROOM,
                    user_id=join_request_data.user_id,
                    room_id=room.id,
                    payload={"room_name": room.name, "username": user.username},
                )
                out_event = OutboxEvent(
                    type=OutboxMessageType.ANALYTICS,
                    status=OutboxStatus.PENDING,
                    payload=event.to_payload(),
                    dedup_key=f"user_join:{room.id}:{join_request_data.user_id}",
                )
                await self._outbox_repo.save(out_event)

            await self._tm.run_in_transaction(_txn)
            logger.bind(room_id=room.id, user_id=join_request_data.user_id).info(
                "User joined public room"
            )

        already_requested = await self._join_repo.exists(
            room_id=room.id, user_id=join_request_data.user_id
        )
        if already_requested:
            raise JoinRequestAlreadyExists

        async def _txn():
            request = JoinRequest(
                room_id=room.id,
                user_id=join_request_data.user_id,
                status=JoinRequestStatus.PENDING,
                message=join_request_data.message,
            )
            await self._join_repo.save(request)

            notif = Notification(
                user_id=room.created_by,
                type=NotificationType.JOIN_REQUEST_CREATED,
                payload={"room_name": room.name, "username": user.username},
                source_id=join_request_data.user_id,
            )
            notif_out = OutboxEvent(
                type=OutboxMessageType.NOTIFICATION,
                status=OutboxStatus.PENDING,
                payload=notif.to_payload(),
                dedup_key=f"notif_joinreq:{room.id}:{join_request_data.user_id}",
            )
            await self._outbox_repo.save(notif_out)

            event = AnalyticsEvent(
                event_type=AnalyticsEventType.JOIN_REQUEST_CREATED,
                user_id=join_request_data.user_id,
                room_id=room.id,
                payload={"room_name": room.name, "username": user.username},
            )
            event_out = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"joinreq_created:{room.id}:{join_request_data.user_id}",
            )
            await self._outbox_repo.save(event_out)

        await self._tm.run_in_transaction(_txn)
        logger.bind(
            room_id=join_request_data.room_id, user_id=join_request_data.user_id
        ).info("Join request created")

    async def handle_join_request(self, request_id: UUID, accept: bool) -> None:
        request = await self._join_repo.get(request_id)
        if not request:
            raise JoinRequestNotFound

        room = await self._room_repo.get(room_id=request.room_id)
        if room is None:
            raise RoomNotFound

        async def _txn():
            if accept:
                await self._add_participant(request.room_id, request.user_id)
                request.status = JoinRequestStatus.ACCEPTED
                notif_type = NotificationType.JOIN_REQUEST_ACCEPTED
                event_type = AnalyticsEventType.JOIN_REQUEST_ACCEPTED
            else:
                request.status = JoinRequestStatus.REJECTED
                notif_type = NotificationType.JOIN_REQUEST_REJECTED
                event_type = AnalyticsEventType.JOIN_REQUEST_ACCEPTED

            request.updated_at = datetime.now(timezone.utc)
            request.handled_by = room.created_by
            await self._join_repo.update(request)

            notif = Notification(
                user_id=request.user_id,
                type=notif_type,
                payload={"room_name": room.name},
                source_id=room.created_by,
            )
            notif_out = OutboxEvent(
                type=OutboxMessageType.NOTIFICATION,
                status=OutboxStatus.PENDING,
                payload=notif.to_payload(),
                dedup_key=f"joinreq_handled:{request.id}",
            )
            await self._outbox_repo.save(notif_out)

            event = AnalyticsEvent(
                event_type=event_type,
                user_id=request.user_id,
                room_id=request.room_id,
                payload={"room_name": room.name},
            )
            event_out = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"analytics_joinreq:{request.id}",
            )
            await self._outbox_repo.save(event_out)

        await self._tm.run_in_transaction(_txn)
        logger.bind(request_id=request_id, status=request.status).info(
            "Join request handled"
        )

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
        return None

    async def remove_participant(self, room_id: UUID, user_id: UUID) -> None:
        room = await self._room_repo.get(room_id=room_id)
        if room is None:
            raise RoomNotFound

        async def _txn():
            await self._membership_repo.delete(room_id=room_id, user_id=user_id)

            if user_id == room.created_by:
                await self._room_repo.delete_by_id(room_id=room_id)
                event_type = AnalyticsEventType.ROOM_DELETED
                logger.bind(room_id=room_id, user_id=user_id).info(
                    "Room was deleted as creator left"
                )
            else:
                await self._room_repo.remove_participant(room_id, user_id)
                event_type = AnalyticsEventType.USER_LEFT_ROOM
                logger.bind(room_id=room_id, user_id=user_id).info(
                    "User removed from room"
                )

            event = AnalyticsEvent(
                event_type=event_type,
                user_id=user_id,
                room_id=room_id,
            )
            out_event = OutboxEvent(
                type=OutboxMessageType.ANALYTICS,
                status=OutboxStatus.PENDING,
                payload=event.to_payload(),
                dedup_key=f"user_left:{room_id}:{user_id}",
            )
            await self._outbox_repo.save(out_event)

        await self._tm.run_in_transaction(_txn)

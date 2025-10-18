from datetime import timezone, datetime
from typing import Any
from uuid import UUID

import structlog

from app.core.constants import (
    JoinRequestStatus,
    NotificationType,
    AnalyticsEventType,
    RoomRole,
)
from app.domain.dtos.join_request import JoinRequestCreateDTO, JoinRequestPublicDTO
from app.domain.dtos.room import (
    RoomCreateDTO,
    RoomPublicDTO,
    RoomUpdateDTO,
    room_to_dto,
)
from app.domain.dtos.user import user_to_dto, UserPublicDTO
from app.domain.entities.join_request import JoinRequest
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
from app.domain.ports.transaction_manager import TransactionManager
from app.domain.repos.join_request import JoinRequestRepository
from app.domain.repos.outbox import OutboxRepository
from app.domain.repos.room import RoomRepository
from app.domain.repos.room_membership import RoomMembershipRepository
from app.domain.repos.user import UserRepository
from app.domain.services.utils import (
    create_outbox_analytics_event,
    create_outbox_notification_event,
)

logger = structlog.get_logger(__name__)


class RoomService:
    def __init__(
        self,
        room_repo: RoomRepository,
        user_repo: UserRepository,
        join_request_repo: JoinRequestRepository,
        room_membership_repo: RoomMembershipRepository,
        outbox_repo: OutboxRepository,
        analytics_port: AnalyticsPort,
        transaction_manager: TransactionManager,
    ):
        self._room_repo = room_repo
        self._user_repo = user_repo
        self._join_repo = join_request_repo
        self._membership_repo = room_membership_repo
        self._outbox_repo = outbox_repo
        self._analytics = analytics_port
        self._tm = transaction_manager

    async def create_room(self, room_data: RoomCreateDTO) -> RoomPublicDTO:
        if await self._room_repo.exists(name=room_data.name):
            raise RoomAlreadyExists

        if not await self._user_repo.get_by_id(user_id=room_data.created_by):
            raise UserNotFound

        async def _txn(db_session: Any) -> Room:
            room = Room(
                name=room_data.name,
                description=room_data.description,
                is_public=room_data.is_public,
                created_by=room_data.created_by,
                participants_count=0,
            )
            room = await self._room_repo.save(room=room, db_session=db_session)
            await self._add_participant(
                room_id=room.id,
                user_id=room_data.created_by,
                role=RoomRole.OWNER,
                db_session=db_session,
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.ROOM_CREATED,
                user_id=room_data.created_by,
                room_id=room.id,
                payload={"room_name": room.name},
                dedup_key=f"room_created:{room.id}",
                db_session=db_session,
            )
            logger.bind(room_id=room.id).info("Room created")

            return room

        room_create = await self._tm.run_in_transaction(_txn)

        return room_to_dto(room=room_create)

    async def update_room(
        self, room_id: UUID, room_data: RoomUpdateDTO
    ) -> RoomPublicDTO:
        room = await self._room_repo.get_by_id(room_id=room_id)
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

        async def _txn(db_session: Any) -> Room:
            room.updated_at = datetime.now(timezone.utc)
            room_saved = await self._room_repo.save(room=room, db_session=db_session)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.ROOM_UPDATED,
                user_id=room.created_by,
                room_id=room.id,
                payload={"room_name": room.name},
                dedup_key=f"room_update:{room.id}:{room.updated_at.timestamp()}",
                db_session=db_session,
            )
            logger.bind(room_id=room.id).info("Room updated")

            return room_saved

        room_update = await self._tm.run_in_transaction(_txn)

        return room_to_dto(room=room_update)

    async def delete_room(self, room_id: UUID) -> None:
        room = await self._room_repo.get_by_id(room_id=room_id)
        if not room:
            raise RoomNotFound

        async def _txn(db_session: Any) -> None:
            await self._room_repo.delete_by_id(room_id=room_id, db_session=db_session)

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.ROOM_DELETED,
                user_id=room.created_by,
                room_id=room.id,
                payload={"room_name": room.name},
                dedup_key=f"room_deleted:{room.id}",
                db_session=db_session,
            )

            logger.bind(room_id=room_id).info("Room deleted")

        await self._tm.run_in_transaction(_txn)

    async def get_room(self, room_id: UUID) -> RoomPublicDTO:
        room = await self._room_repo.get_by_id(room_id=room_id)
        if room is None:
            raise RoomNotFound
        return room_to_dto(room=room)

    async def list_room_users(self, room_id: UUID) -> list[UserPublicDTO]:
        users = await self._membership_repo.list_users(room_id=room_id)
        return [user_to_dto(user=user) for user in users]

    async def list_rooms_for_user(self, user_id: UUID) -> list[RoomPublicDTO]:
        rooms = await self._membership_repo.list_rooms_for_user(user_id=user_id)
        return [room_to_dto(room=room) for room in rooms]

    async def list_top_rooms(
        self, limit: int, only_public: bool
    ) -> list[RoomPublicDTO]:
        rooms = await self._room_repo.list_top_room(
            limit=limit, only_public=only_public
        )
        return [room_to_dto(room) for room in rooms]

    async def list_room_join_requests(
        self, room_id: UUID
    ) -> list[JoinRequestPublicDTO]:
        join_requests = await self._join_repo.list_by_room(
            room_id=room_id, status=JoinRequestStatus.PENDING
        )
        if not join_requests:
            return []

        return [
            JoinRequestPublicDTO(
                username=user.username,
                room_name=room.name,
                message=join_request.message,
            )
            for join_request, user, room in join_requests
        ]

    async def list_user_join_requests(
        self, user_id: UUID
    ) -> list[JoinRequestPublicDTO]:
        join_requests = await self._join_repo.list_by_user(
            user_id=user_id, status=JoinRequestStatus.PENDING
        )
        if not join_requests:
            return []

        return [
            JoinRequestPublicDTO(
                username=user.username,
                room_name=room.name,
                message=join_request.message,
            )
            for join_request, user, room in join_requests
        ]

    async def search_rooms(self, query: str, limit: int) -> list[RoomPublicDTO]:
        rooms = await self._room_repo.search(query=query, limit=limit)
        return [room_to_dto(room=room) for room in rooms]

    async def request_join(self, join_request_data: JoinRequestCreateDTO) -> None:
        room = await self._room_repo.get_by_id(room_id=join_request_data.room_id)
        if not room:
            raise RoomNotFound

        user = await self._user_repo.get_by_id(user_id=join_request_data.user_id)
        if user is None:
            raise UserNotFound

        if room.is_public:

            async def _txn(db_session: Any) -> None:
                await self._add_participant(
                    room_id=room.id,
                    user_id=join_request_data.user_id,
                    role=RoomRole.MEMBER,
                    db_session=db_session,
                )

                await create_outbox_analytics_event(
                    outbox_repo=self._outbox_repo,
                    event_type=AnalyticsEventType.USER_JOINED_ROOM,
                    user_id=join_request_data.user_id,
                    room_id=room.id,
                    payload={"room_name": room.name, "username": user.username},
                    dedup_key=f"user_join:{room.id}:{join_request_data.user_id}",
                    db_session=db_session,
                )

                logger.bind(room_id=room.id, user_id=join_request_data.user_id).info(
                    "User joined public room"
                )

            await self._tm.run_in_transaction(_txn)
            return None

        already_requested = await self._join_repo.exists(
            room_id=room.id, user_id=join_request_data.user_id
        )
        if already_requested:
            raise JoinRequestAlreadyExists

        async def __txn(db_session: Any) -> None:
            request = JoinRequest(
                room_id=room.id,
                user_id=join_request_data.user_id,
                status=JoinRequestStatus.PENDING,
                message=join_request_data.message,
            )
            await self._join_repo.save(request=request, db_session=db_session)

            await create_outbox_notification_event(
                outbox_repo=self._outbox_repo,
                notification_type=NotificationType.JOIN_REQUEST_CREATED,
                user_id=room.created_by,
                source_id=join_request_data.user_id,
                payload={"room_name": room.name, "username": user.username},
                dedup_key=f"notif_joinreq:{room.id}:{join_request_data.user_id}",
                db_session=db_session,
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=AnalyticsEventType.JOIN_REQUEST_CREATED,
                user_id=join_request_data.user_id,
                room_id=room.id,
                payload={"room_name": room.name, "username": user.username},
                dedup_key=f"joinreq_created:{room.id}:{join_request_data.user_id}",
                db_session=db_session,
            )

            logger.bind(
                room_id=join_request_data.room_id, user_id=join_request_data.user_id
            ).info("Join request created")

        await self._tm.run_in_transaction(__txn)

    async def handle_join_request(self, request_id: UUID, accept: bool) -> None:
        request = await self._join_repo.get_by_id(request_id=request_id)
        if not request:
            raise JoinRequestNotFound

        room = await self._room_repo.get_by_id(room_id=request.room_id)
        if room is None:
            raise RoomNotFound

        async def _txn(db_session: Any) -> None:
            if accept:
                await self._add_participant(
                    room_id=request.room_id,
                    user_id=request.user_id,
                    db_session=db_session,
                )
                request.status = JoinRequestStatus.ACCEPTED
                notif_type = NotificationType.JOIN_REQUEST_ACCEPTED
                event_type = AnalyticsEventType.JOIN_REQUEST_ACCEPTED
            else:
                request.status = JoinRequestStatus.REJECTED
                notif_type = NotificationType.JOIN_REQUEST_REJECTED
                event_type = AnalyticsEventType.JOIN_REQUEST_REJECTED

            request.updated_at = datetime.now(timezone.utc)
            request.handled_by = room.created_by
            await self._join_repo.save(request=request, db_session=db_session)

            await create_outbox_notification_event(
                outbox_repo=self._outbox_repo,
                notification_type=notif_type,
                user_id=request.user_id,
                source_id=room.created_by,
                payload={"room_name": room.name},
                dedup_key=f"joinreq_handled:{request.id}",
                db_session=db_session,
            )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=event_type,
                user_id=request.user_id,
                room_id=request.room_id,
                payload={"room_name": room.name},
                dedup_key=f"analytics_joinreq:{request.id}",
                db_session=db_session,
            )

            logger.bind(request_id=request_id, status=request.status).info(
                "Join request handled"
            )

        await self._tm.run_in_transaction(_txn)

    async def _add_participant(
        self,
        room_id: UUID,
        user_id: UUID,
        role: RoomRole = RoomRole.MEMBER,
        db_session: Any | None = None,
    ) -> None:
        exists = await self._membership_repo.exists(
            room_id=room_id, user_id=user_id, db_session=db_session
        )
        if exists:
            return None

        room_membership = RoomMembership(
            room_id=room_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.now(timezone.utc),
        )
        await self._membership_repo.save(
            room_membership=room_membership, db_session=db_session
        )
        await self._room_repo.add_participant(room_id=room_id, db_session=db_session)
        logger.bind(room_id=room_id, user_id=user_id).info("User added to room")

        return None

    async def remove_participant(self, room_id: UUID, user_id: UUID) -> None:
        room = await self._room_repo.get_by_id(room_id=room_id)
        if room is None:
            raise RoomNotFound

        async def _txn(db_session: Any) -> None:
            await self._membership_repo.delete(
                room_id=room_id, user_id=user_id, db_session=db_session
            )

            if user_id == room.created_by:
                await self._room_repo.delete_by_id(
                    room_id=room_id, db_session=db_session
                )
                event_type = AnalyticsEventType.ROOM_DELETED
                logger.bind(room_id=room_id, user_id=user_id).info(
                    "Room was deleted as creator left"
                )
            else:
                await self._room_repo.remove_participant(
                    room_id=room_id, db_session=db_session
                )
                event_type = AnalyticsEventType.USER_LEFT_ROOM
                logger.bind(room_id=room_id, user_id=user_id).info(
                    "User removed from room"
                )

            await create_outbox_analytics_event(
                outbox_repo=self._outbox_repo,
                event_type=event_type,
                user_id=user_id,
                room_id=room_id,
                dedup_key=f"user_left:{room_id}:{user_id}",
                db_session=db_session,
            )

        await self._tm.run_in_transaction(_txn)

from dataclasses import asdict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status, Response

from app.api.dependencies import get_current_user_id
from app.api.di import get_room_service
from app.api.schemas.room import (
    RoomCreate,
    RoomUpdate,
    RoomPublic,
    SendJoinRequest,
    JoinRequestPublic,
)
from app.api.schemas.user import UserPublic
from app.domain.services.room import RoomService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/create-room")
async def create_room(
    room_data: RoomCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> RoomPublic:
    logger.bind(name=room_data.name, user_id=current_user_id).debug("Creating room...")
    room = await room_service.create_room(
        room_data=room_data.to_dto(created_by=current_user_id)
    )
    logger.bind(room_id=room.id, name=room_data.name, user_id=current_user_id).debug(
        "Room created"
    )
    return RoomPublic.model_validate(asdict(room))


@router.put("/update-room/{room_id}")
async def update_room(
    room_id: UUID,
    room_data: RoomUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> RoomPublic:
    logger.bind(room_id=room_id).debug("Updating room...")
    room = await room_service.update_room(
        room_id=room_id, room_data=room_data.to_dto(created_by=current_user_id)
    )
    logger.bind(room_id=room.id).debug("Room updated")
    return RoomPublic.model_validate(asdict(room))


@router.delete("/delete-room/{room_id}")
async def delete_room(
    room_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> Response:
    logger.bind(room_id=room_id).debug("Deleting room...")
    await room_service.delete_room(room_id=room_id, created_by=current_user_id)
    logger.bind(room_id=room_id).debug("Room deleted")
    return Response(status_code=status.HTTP_200_OK)


@router.get("/get-room/{room_id}", response_model=RoomPublic)
async def get_room(
    room_id: UUID,
    _: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> RoomPublic:
    logger.bind(room_id=room_id).debug("Fetching room...")
    room = await room_service.get_room(room_id=room_id)
    logger.bind(room_id=room.id).debug("Fetched room")
    return RoomPublic.model_validate(asdict(room))


@router.get("/get-users/{room_id}")
async def list_room_users(
    room_id: UUID,
    _: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> list[UserPublic]:
    logger.bind(room_id=room_id).debug("Fetching room users...")
    users = await room_service.list_room_users(room_id=room_id)
    logger.bind(room_id=room_id, count=len(users)).debug("Fetched room users")
    return [UserPublic.model_validate(asdict(user)) for user in users]


@router.get("/get-rooms")
async def list_rooms_for_user(
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> list[RoomPublic]:
    logger.bind(user_id=current_user_id).debug("Fetching user rooms...")
    rooms = await room_service.list_rooms_for_user(user_id=current_user_id)
    logger.bind(user_id=current_user_id, count=len(rooms)).debug("Fetched user rooms")
    return [RoomPublic.model_validate(asdict(room)) for room in rooms]


@router.get("/get-top-rooms")
async def list_top_rooms(
    limit: int = Query(default=10, ge=1, le=100),
    only_public: bool = Query(default=True),
    _: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> list[RoomPublic]:
    logger.bind(limit=limit, only_public=only_public).debug("Fetching top rooms...")
    rooms = await room_service.list_top_rooms(limit=limit, only_public=only_public)
    logger.bind(count=len(rooms)).debug("Fetched top rooms")
    return [RoomPublic.model_validate(asdict(room)) for room in rooms]


@router.get("/get-join-requests-by-room/{room_id}")
async def list_room_join_requests(
    room_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> list[JoinRequestPublic]:
    logger.bind(room_id=room_id).debug("Fetching join requests for room...")
    requests = await room_service.list_room_join_requests(
        room_id=room_id, created_by=current_user_id
    )
    logger.bind(room_id=room_id, count=len(requests)).debug("Fetched join requests")
    return [JoinRequestPublic.model_validate(asdict(request)) for request in requests]


@router.get("/get-join-requests-by-user")
async def list_user_join_requests(
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> list[JoinRequestPublic]:
    logger.bind(user_id=current_user_id).debug("Fetching join requests for user...")
    requests = await room_service.list_user_join_requests(user_id=current_user_id)
    logger.bind(user_id=current_user_id, count=len(requests)).debug(
        "Fetched join requests"
    )
    return [JoinRequestPublic.model_validate(asdict(request)) for request in requests]


@router.get("/get-search-rooms")
async def search_rooms(
    text: str = Query(..., min_length=1, max_length=32),
    limit: int = Query(default=20, ge=1, le=100),
    _: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> list[RoomPublic]:
    logger.bind(query=text, limit=limit).debug("Searching rooms...")
    rooms = await room_service.search_rooms(query=text, limit=limit)
    logger.bind(count=len(rooms)).debug("Rooms search complete")
    return [RoomPublic.model_validate(asdict(room)) for room in rooms]


@router.post("/create-join-request")
async def request_join(
    join_request: SendJoinRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> Response:
    logger.bind(room_id=join_request.room_id, user_id=current_user_id).debug(
        "Creating join request..."
    )
    await room_service.request_join(
        join_request_data=join_request.to_dto(user_id=current_user_id)
    )
    logger.bind(room_id=join_request.room_id, user_id=current_user_id).debug(
        "Join request processed"
    )
    return Response(status_code=status.HTTP_200_OK)


@router.post("/handle-join-request/{request_id}")
async def handle_join_request(
    request_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    accept: bool = Query(default=False),
    room_service: RoomService = Depends(get_room_service),
) -> Response:
    logger.bind(request_id=request_id, accept=accept, user_id=current_user_id).debug(
        "Handling join request..."
    )
    await room_service.handle_join_request(
        request_id=request_id, created_by=current_user_id, accept=accept
    )
    logger.bind(request_id=request_id, accept=accept, user_id=current_user_id).debug(
        "Join request handled"
    )
    return Response(status_code=status.HTTP_200_OK)


@router.delete("/remove-user/{room_id}/{user_id}")
async def remove_participant(
    room_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> Response:
    logger.bind(room_id=room_id, user_id=user_id, created_by=current_user_id).debug(
        "Removing participant..."
    )
    await room_service.remove_participant(
        room_id=room_id, user_id=user_id, created_by=current_user_id
    )
    logger.bind(room_id=room_id, user_id=user_id, created_by=current_user_id).debug(
        "Participant removed"
    )
    return Response(status_code=status.HTTP_200_OK)


@router.delete("/leave-room/{room_id}")
async def leave_room(
    room_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    room_service: RoomService = Depends(get_room_service),
) -> Response:
    logger.bind(room_id=room_id, user_id=current_user_id).debug("Leaving room...")
    await room_service.leave_room(room_id=room_id, user_id=current_user_id)
    logger.bind(room_id=room_id, user_id=current_user_id).debug("Room left")
    return Response(status_code=status.HTTP_200_OK)

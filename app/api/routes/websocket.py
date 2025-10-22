import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Response, WebSocket, status

from app.api.dependencies import get_current_user_id, get_websocket_room_id
from app.api.di import get_websocket_service, get_websocket_service_from_websocket
from app.api.utils import _cleanup_connection, _run_websocket_loop
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.services.websocket import WebSocketService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    room_id: UUID = Depends(get_websocket_room_id),
    ws_service: WebSocketService = Depends(get_websocket_service_from_websocket),
) -> None:
    session_cookie = websocket.cookies.get("session_id")
    user_id = await ws_service.validate_user(session_id=session_cookie, room_id=room_id)
    redis = websocket.app.state.redis

    logger.bind(user_id=user_id, room_id=room_id).debug("Connecting WebSocket")
    await websocket.accept()

    session = WebSocketSession(
        user_id=user_id,
        room_id=room_id,
        connected_at=datetime.now(UTC),
        last_ping_at=datetime.now(UTC),
        ip_address=websocket.client.host if websocket.client else "unknown",
    )
    stop_event = asyncio.Event()
    pubsub: Any | None = None

    try:
        channels = await ws_service.connect_to_room(session=session)
        pubsub = redis.pubsub()
        await pubsub.subscribe(*channels)
        logger.bind(user_id=user_id, session_id=session.id).debug(
            "WebSocket session registered and subscribed to channels"
        )
        await _run_websocket_loop(
            websocket=websocket,
            ws_service=ws_service,
            pubsub=pubsub,
            session=session,
            user_id=user_id,
            room_id=room_id,
            stop_event=stop_event,
        )

    except Exception as e:
        logger.bind(user_id=user_id, session_id=session.id, e=str(e)).info(
            "WebSocket error"
        )
    finally:
        await _cleanup_connection(
            ws_service=ws_service,
            session=session,
            user_id=user_id,
            pubsub=pubsub,
            stop_event=stop_event,
        )


@router.get("/get-active-user-ids/{room_id}")
async def get_active_users_in_room(
    room_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> list[UUID]:
    logger.bind(user_id=current_user_id, room_id=room_id).debug(
        "Fetching active users in room"
    )
    users = await ws_service.active_users_in_room(
        room_id=room_id, user_id=current_user_id
    )
    logger.bind(user_id=current_user_id, room_id=room_id, count=len(users)).debug(
        "Fetched active users"
    )
    return users


@router.delete("/disconnect-user/{room_id}/{user_id}")
async def disconnect_user_from_room(
    room_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> Response:
    logger.bind(user_id=current_user_id, target_user_id=user_id, room_id=room_id).debug(
        "Disconnecting user from room"
    )
    await ws_service.disconnect_user_from_room(
        user_id=user_id, room_id=room_id, created_by=current_user_id
    )
    logger.bind(user_id=current_user_id, target_user_id=user_id, room_id=room_id).debug(
        "User disconnected from room"
    )
    return Response(status_code=status.HTTP_200_OK)

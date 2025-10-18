import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Response, status
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.api.dependencies import get_current_user_id, get_current_session_id
from app.api.di import get_websocket_service, get_redis
from app.api.schemas.websocket import TypingPayload
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.exceptions.websocket_session import (
    WebSocketSessionNotFound,
    WebSocketSessionPermissionError,
)
from app.domain.services.websocket import WebSocketService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    room_id: UUID,
    redis: Redis = Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
    current_session_id: UUID = Depends(get_current_session_id),
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> None:
    await websocket.accept()
    stop_event = asyncio.Event()

    session = WebSocketSession(
        user_id=current_user_id,
        room_id=room_id,
        session_id=current_session_id,
        connected_at=datetime.now(timezone.utc),
        last_ping_at=datetime.now(timezone.utc),
        ip_address=websocket.client.host if websocket.client else "unknown",
    )

    await ws_service.connect(session=session)

    pubsub = redis.pubsub()
    user_rooms_key = f"ws:user:{current_user_id}:rooms"
    room_ids: set[str] = await redis.smembers(user_rooms_key)  # type: ignore
    channels = [f"ws:user:{current_user_id}:notifications"] + [
        f"ws:room:{rid}" for rid in room_ids
    ]
    await pubsub.subscribe(*channels)

    async def ping_loop() -> None:
        while not stop_event.is_set():
            await asyncio.sleep(30)
            try:
                await ws_service.update_ping(
                    session_id=session.id, user_id=current_user_id
                )
            except (WebSocketSessionNotFound, WebSocketSessionPermissionError):
                stop_event.set()
            except Exception as e:
                logger.warning("Ping update failed", error=str(e))
                await asyncio.sleep(5)

    async def listen_redis() -> None:
        while not stop_event.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message:
                await websocket.send_text(message["data"].decode())
            await asyncio.sleep(0.01)

    try:
        await asyncio.gather(ping_loop(), listen_redis())
    except WebSocketDisconnect:
        logger.bind(user_id=current_user_id).info("WebSocket disconnected by client")
    finally:
        stop_event.set()
        await ws_service.disconnect(session_id=session.id, user_id=current_user_id)
        with suppress(Exception):
            await pubsub.unsubscribe(*channels)
            await pubsub.close()


async def _ping_loop(
    ws_service: WebSocketService, session_id: UUID, user_id: UUID
) -> None:
    while True:
        await asyncio.sleep(30)
        try:
            await ws_service.update_ping(session_id=session_id, user_id=user_id)
        except (WebSocketSessionNotFound, WebSocketSessionPermissionError):
            break
        except Exception as e:
            logger.warning("Ping update failed", error=str(e))
            await asyncio.sleep(5)


async def _listen_redis(pubsub: PubSub, websocket: WebSocket) -> None:
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if message:
            await websocket.send_text(message["data"].decode())
        await asyncio.sleep(0.01)


@router.post("/typing")
async def typing_indicator(
    payload: TypingPayload,
    current_user_id: UUID = Depends(get_current_user_id),
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> Response:
    await ws_service.typing_indicator(
        room_id=payload.room_id,
        user_id=current_user_id,
        username=payload.username,
        is_typing=payload.is_typing,
    )
    return Response(status_code=status.HTTP_200_OK)


@router.get("/get-active-user-ids/{room_id}")
async def get_active_users_in_room(
    room_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> list[UUID]:
    return await ws_service.count_active_users_in_room(
        room_id=room_id, user_id=current_user_id
    )


@router.post("/disconnect-user/{room_id}/{user_id}")
async def disconnect_user_from_room(
    room_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> Response:
    await ws_service.disconnect_user_from_room(
        user_id=user_id, room_id=room_id, created_by=current_user_id
    )
    return Response(status_code=status.HTTP_200_OK)


@router.get("/get-user-is-online/{user_id}")
async def is_user_online(
    user_id: UUID,
    ws_service: WebSocketService = Depends(get_websocket_service),
) -> bool:
    return await ws_service.is_user_online(user_id=user_id)

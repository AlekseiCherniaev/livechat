import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import orjson
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Response, status

from app.api.dependencies import get_current_user_id, get_websocket_room_id
from app.api.di import get_websocket_service, get_websocket_service_from_websocket
from app.core.constants import BroadcastEventType
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
    room_id: UUID = Depends(get_websocket_room_id),
    ws_service: WebSocketService = Depends(get_websocket_service_from_websocket),
) -> None:
    session_cookie = websocket.cookies.get("session_id")
    user_id = await ws_service.validate_user(session_id=session_cookie, room_id=room_id)
    redis = websocket.app.state.redis
    logger.bind(user_id=user_id, room_id=room_id).debug("Connecting WebSocket")

    await websocket.accept()
    stop_event = asyncio.Event()

    logger.bind(user_id=user_id, room_id=room_id).debug(
        "WebSocket connection established"
    )

    session = WebSocketSession(
        user_id=user_id,
        room_id=room_id,
        connected_at=datetime.now(timezone.utc),
        last_ping_at=datetime.now(timezone.utc),
        ip_address=websocket.client.host if websocket.client else "unknown",
    )

    pubsub: Any | None = None
    try:
        channels = await ws_service.connect_to_room(session=session)
        logger.bind(user_id=user_id, session_id=session.id).debug(
            "WebSocket session registered"
        )

        pubsub = redis.pubsub()
        await pubsub.subscribe(*channels)
        logger.bind(user_id=user_id, room_id=room_id, channels=channels).debug(
            "Subscribed to Redis channels"
        )

        async def ping_loop() -> None:
            while not stop_event.is_set():
                try:
                    await asyncio.sleep(30)
                    if stop_event.is_set():
                        break

                    await ws_service.update_ping(session_id=session.id, user_id=user_id)
                    try:
                        await websocket.send_json({"type": "PING"})
                    except (WebSocketDisconnect, RuntimeError):
                        stop_event.set()
                        break

                except (WebSocketSessionNotFound, WebSocketSessionPermissionError):
                    logger.bind(user_id=user_id, session_id=session.id).warning(
                        "Ping failed, closing WebSocket"
                    )
                    stop_event.set()
                    break
                except Exception as err:
                    logger.bind(user_id=user_id, error=str(err)).warning(
                        "Ping update failed"
                    )
                    await asyncio.sleep(5)

        async def listen_redis() -> None:
            while not stop_event.is_set():
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message and message["type"] == "message":
                        try:
                            await websocket.send_text(message["data"])
                        except WebSocketDisconnect:
                            logger.debug("WebSocket disconnected during send")
                            break
                        except RuntimeError as err:
                            if "WebSocket is not connected" in str(err):
                                break
                            raise

                except asyncio.CancelledError:
                    break
                except Exception as err:
                    if not stop_event.is_set():
                        logger.error(f"Redis listen error: {err}")
                    await asyncio.sleep(0.1)

        async def handle_client_messages() -> None:
            while not stop_event.is_set():
                try:
                    message_data = await websocket.receive_text()
                    data = orjson.loads(message_data)
                    message_type = data.get("type")

                    if message_type == "PONG":
                        continue
                    elif message_type == BroadcastEventType.USER_TYPING.value:
                        await ws_service.typing_indicator(
                            room_id=room_id,
                            user_id=user_id,
                            username=data.get("username", ""),
                            is_typing=data.get("is_typing", False),
                        )
                        logger.bind(user_id=user_id).debug("Typing indicator processed")
                    else:
                        logger.bind(user_id=user_id).warning(
                            f"Unknown message type: {message_type}"
                        )

                except WebSocketDisconnect:
                    logger.bind(user_id=user_id).debug(
                        "WebSocket disconnected in message handler"
                    )
                    break
                except Exception as err:
                    logger.bind(user_id=user_id, error=str(err)).error(
                        "Error handling client message"
                    )
                    await asyncio.sleep(0.1)

        tasks = [
            asyncio.create_task(ping_loop()),
            asyncio.create_task(listen_redis()),
            asyncio.create_task(handle_client_messages()),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        logger.bind(user_id=user_id, session_id=session.id, e=str(e)).info(
            "WebSocket error"
        )
    finally:
        stop_event.set()
        await ws_service.disconnect_from_room(session_id=session.id, user_id=user_id)
        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.close()


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

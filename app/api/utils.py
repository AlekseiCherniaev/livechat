import asyncio
from typing import Any
from uuid import UUID

import orjson
import structlog
from fastapi import WebSocket, WebSocketDisconnect

from app.core.constants import BroadcastEventType
from app.domain.entities.websocket_session import WebSocketSession
from app.domain.exceptions.websocket_session import (
    WebSocketSessionNotFound,
    WebSocketSessionPermissionError,
)
from app.domain.services.websocket import WebSocketService

logger = structlog.get_logger(__name__)


async def _run_websocket_loop(
    websocket: WebSocket,
    ws_service: WebSocketService,
    pubsub: Any,
    session: WebSocketSession,
    user_id: UUID,
    room_id: UUID,
    stop_event: asyncio.Event,
) -> None:
    tasks = [
        asyncio.create_task(
            _ping_loop(websocket, ws_service, session, user_id, stop_event)
        ),
        asyncio.create_task(_listen_redis_messages(websocket, pubsub, stop_event)),
        asyncio.create_task(
            _handle_client_messages(websocket, ws_service, user_id, room_id, stop_event)
        ),
    ]

    await asyncio.gather(*tasks, return_exceptions=True)


async def _ping_loop(
    websocket: WebSocket,
    ws_service: WebSocketService,
    session: WebSocketSession,
    user_id: UUID,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.sleep(30)
            if stop_event.is_set():
                break

            await ws_service.update_ping(session_id=session.id, user_id=user_id)
            await websocket.send_json({"type": "PING"})

        except (WebSocketSessionNotFound, WebSocketSessionPermissionError):
            logger.bind(user_id=user_id, session_id=session.id).warning(
                "Ping failed - session invalid, closing WebSocket"
            )
            stop_event.set()
            break
        except (WebSocketDisconnect, RuntimeError):
            logger.bind(user_id=user_id).debug("WebSocket disconnected during ping")
            stop_event.set()
            break
        except Exception as err:
            logger.bind(user_id=user_id, error=str(err)).warning("Ping update failed")
            await asyncio.sleep(5)


async def _listen_redis_messages(
    websocket: WebSocket, pubsub: Any, stop_event: asyncio.Event
) -> None:
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


async def _handle_client_messages(
    websocket: WebSocket,
    ws_service: WebSocketService,
    user_id: UUID,
    room_id: UUID,
    stop_event: asyncio.Event,
) -> None:
    while not stop_event.is_set():
        try:
            message_data = await websocket.receive_text()
            data = orjson.loads(message_data)
            message_type = data.get("type")

            if message_type == "PONG":
                continue
            if message_type == BroadcastEventType.USER_TYPING.value:
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
            logger.bind(user_id=user_id).debug("WebSocket disconnected")
            break
        except Exception as err:
            logger.bind(user_id=user_id, error=str(err)).error(
                "Error handling client message"
            )
            await asyncio.sleep(0.1)


async def _cleanup_connection(
    ws_service: WebSocketService,
    session: WebSocketSession,
    user_id: UUID,
    pubsub: Any | None,
    stop_event: asyncio.Event,
) -> None:
    stop_event.set()

    try:
        await ws_service.disconnect_from_room(session_id=session.id, user_id=user_id)
    except Exception as e:
        logger.bind(user_id=user_id, session_id=session.id, error=str(e)).error(
            "Error during WebSocket disconnect"
        )

    if pubsub:
        try:
            await pubsub.unsubscribe()
            await pubsub.close()
        except Exception as e:
            logger.bind(user_id=user_id, error=str(e)).error(
                "Error during Redis pubsub cleanup"
            )

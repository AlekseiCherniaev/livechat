from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status, Response

from app.api.di import get_message_service
from app.api.schemas.message import (
    SendMessageRequest,
    EditMessageRequest,
    DeleteMessageRequest,
    MessagePublic,
)
from app.domain.services.message import MessageService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/{room_id}")
async def send_message(
    room_id: UUID,
    message_request: SendMessageRequest,
    message_service: MessageService = Depends(get_message_service),
) -> Response:
    logger.bind(room_id=room_id, user_id=message_request.user_id).debug(
        "Sending message..."
    )
    await message_service.send_message(
        room_id=room_id,
        user_id=message_request.user_id,
        content=message_request.content,
    )
    logger.bind(room_id=room_id, user_id=message_request.user_id).debug("Message sent")
    return Response(status_code=status.HTTP_200_OK)


@router.patch("/{message_id}")
async def edit_message(
    message_id: UUID,
    message_request: EditMessageRequest,
    message_service: MessageService = Depends(get_message_service),
) -> Response:
    logger.bind(message_id=message_id, user_id=message_request.user_id).debug(
        "Editing message..."
    )
    await message_service.edit_message(
        message_id=message_id,
        user_id=message_request.user_id,
        new_content=message_request.new_content,
    )
    logger.bind(message_id=message_id, user_id=message_request.user_id).debug(
        "Message edited"
    )
    return Response(status_code=status.HTTP_200_OK)


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    message_request: DeleteMessageRequest,
    message_service: MessageService = Depends(get_message_service),
) -> Response:
    logger.bind(message_id=message_id, user_id=message_request.user_id).debug(
        "Deleting message..."
    )
    await message_service.delete_message(
        message_id=message_id, user_id=message_request.user_id
    )
    logger.bind(message_id=message_id, user_id=message_request.user_id).debug(
        "Message deleted"
    )
    return Response(status_code=status.HTTP_200_OK)


@router.get("/{room_id}/recent")
async def get_recent_messages(
    room_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    message_service: MessageService = Depends(get_message_service),
) -> list[MessagePublic]:
    logger.bind(room_id=room_id, limit=limit).debug("Fetching recent messages...")
    messages = await message_service.get_recent_messages(room_id=room_id, limit=limit)
    logger.bind(room_id=room_id, count=len(messages)).debug("Fetched recent messages")
    return [MessagePublic.model_validate(message) for message in messages]


@router.get("/user/{user_id}")
async def get_user_messages(
    user_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    message_service: MessageService = Depends(get_message_service),
) -> list[MessagePublic]:
    logger.bind(user_id=user_id, limit=limit).debug("Fetching user messages...")
    messages = await message_service.get_user_messages(user_id=user_id, limit=limit)
    logger.bind(user_id=user_id, count=len(messages)).debug("Fetched user messages")
    return [MessagePublic.model_validate(message) for message in messages]

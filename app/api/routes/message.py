from dataclasses import asdict
from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query, status, Response

from app.api.dependencies import get_current_user_id
from app.api.di import get_message_service
from app.api.schemas.message import (
    SendMessageRequest,
    EditMessageRequest,
    MessagePublic,
)
from app.domain.services.message import MessageService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/create-message/{room_id}")
async def send_message(
    room_id: UUID,
    message_data: SendMessageRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessagePublic:
    logger.bind(room_id=room_id, user_id=current_user_id).debug("Sending message...")
    message = await message_service.send_message(
        room_id=room_id,
        user_id=current_user_id,
        content=message_data.content,
    )
    logger.bind(room_id=room_id, user_id=current_user_id).debug("Message sent")
    return MessagePublic.model_validate(asdict(message))


@router.put("/update-message/{message_id}")
async def edit_message(
    message_id: UUID,
    message_data: EditMessageRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessagePublic:
    logger.bind(message_id=message_id, user_id=current_user_id).debug(
        "Editing message..."
    )
    message = await message_service.edit_message(
        message_id=message_id,
        user_id=current_user_id,
        new_content=message_data.new_content,
    )
    logger.bind(message_id=message_id, user_id=current_user_id).debug("Message edited")
    return MessagePublic.model_validate(asdict(message))


@router.delete("/delete-message/{message_id}")
async def delete_message(
    message_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> Response:
    logger.bind(message_id=message_id, user_id=current_user_id).debug(
        "Deleting message..."
    )
    await message_service.delete_message(message_id=message_id, user_id=current_user_id)
    logger.bind(message_id=message_id, user_id=current_user_id).debug("Message deleted")
    return Response(status_code=status.HTTP_200_OK)


@router.get("/get-recent-messages/{room_id}")
async def get_recent_messages(
    room_id: UUID,
    before: datetime | None = Query(None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> list[MessagePublic]:
    logger.bind(room_id=room_id, limit=limit, user_id=current_user_id).debug(
        "Fetching recent messages..."
    )
    messages = await message_service.get_recent_messages(
        room_id=room_id, limit=limit, before=before, user_id=current_user_id
    )
    logger.bind(room_id=room_id, count=len(messages), user_id=current_user_id).debug(
        "Fetched recent messages"
    )
    return [MessagePublic.model_validate(asdict(message)) for message in messages]

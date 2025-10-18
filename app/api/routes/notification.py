from dataclasses import asdict
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Response, status, Query

from app.api.dependencies import get_current_user_id
from app.api.di import get_notification_service
from app.api.schemas.notification import (
    NotificationListResponse,
    NotificationCountResponse,
    NotificationPublic,
)
from app.domain.services.notification import NotificationService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    user_id: UUID = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    logger.bind(user_id=user_id, unread_only=unread_only, limit=limit).debug(
        "Fetching user notifications..."
    )
    notifications = await notification_service.list_user_notifications(
        user_id=user_id, unread_only=unread_only, limit=limit
    )
    logger.bind(user_id=user_id, amount=len(notifications)).debug(
        "Fetched user notifications"
    )
    return NotificationListResponse(
        notifications=[
            NotificationPublic.model_validate(asdict(notification))
            for notification in notifications
        ]
    )


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: UUID,
    notification_service: NotificationService = Depends(get_notification_service),
    _: UUID = Depends(get_current_user_id),
) -> Response:
    logger.bind(notification_id=notification_id).debug(
        "Marking notification as read..."
    )
    await notification_service.mark_as_read(notification_id=notification_id)
    logger.bind(notification_id=notification_id).info("Notification marked as read")
    return Response(status_code=status.HTTP_200_OK)


@router.post("/read-all")
async def mark_all_as_read(
    user_id: UUID = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
) -> Response:
    logger.bind(user_id=user_id).debug("Marking all notifications as read...")
    await notification_service.mark_all_as_read(user_id=user_id)
    logger.bind(user_id=user_id).info("All notifications marked as read")
    return Response(status_code=status.HTTP_200_OK)


@router.get("/count")
async def count_unread(
    user_id: UUID = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationCountResponse:
    logger.bind(user_id=user_id).debug("Counting unread notifications...")
    unread_count = await notification_service.count_unread(user_id=user_id)
    logger.bind(user_id=user_id, unread_count=unread_count).debug(
        "Fetched unread notification count"
    )
    return NotificationCountResponse(unread_count=unread_count)

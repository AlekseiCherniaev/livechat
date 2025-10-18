from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user_id
from app.api.di import get_analytics_service
from app.domain.entities.room_stats import RoomStats
from app.domain.services.analytics import AnalyticsService

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user_id)]
)


@router.get("/get-room-stats")
async def room_stats(
    room_id: UUID, analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> RoomStats:
    return await analytics_service.room_stats(room_id=room_id)


@router.get("/get-user-activity")
async def user_activity(
    user_id: UUID, analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> dict[str, int]:
    return await analytics_service.user_activity(user_id=user_id)


@router.get("/get-top-active-rooms")
async def top_active_rooms(
    limit: int = Query(default=50, ge=1, le=200),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[RoomStats]:
    return await analytics_service.top_active_rooms(limit=limit)


@router.get("/get-message-per-minutes")
async def messages_per_minute(
    room_id: UUID,
    since_minutes: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> int:
    return await analytics_service.messages_per_minute(
        room_id=room_id, since_minutes=since_minutes
    )


@router.get("/get-user-retention")
async def user_retention(
    days: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> float:
    return await analytics_service.user_retention(days=days)


@router.get("/get-message-edit-delete-ratio")
async def message_edit_delete_ratio(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, float]:
    return await analytics_service.message_edit_delete_ratio()


@router.get("/get-top-social-users")
async def top_social_users(
    limit: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict[str, Any]]:
    return await analytics_service.top_social_users(limit=limit)

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query

from app.api.di import get_analytics_service
from app.domain.entities.room_stats import RoomStats
from app.domain.services.analytics import AnalyticsService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/get-room-stats")
async def get_room_stats(
    room_id: UUID, analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> RoomStats:
    return await analytics_service.get_room_stats(room_id=room_id)


@router.get("/get-user-activity")
async def get_user_activity(
    user_id: UUID, analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> dict[str, int]:
    return await analytics_service.get_user_activity(user_id=user_id)


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

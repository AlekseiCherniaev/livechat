from dataclasses import asdict
from uuid import UUID

import structlog
from fastapi import Response, Request, Depends

from app.api.di import get_user_service
from app.api.schemas.user import UserPublic
from app.core.constants import Environment
from app.core.settings import get_settings
from app.domain.services.user import UserService

logger = structlog.get_logger(__name__)


def set_session_cookie(response: Response, session_id: str) -> None:
    is_production = get_settings().environment == Environment.PROD

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
        max_age=get_settings().user_session_ttl_seconds,
    )


async def get_current_user(
    request: Request, user_service: UserService = Depends(get_user_service)
) -> UserPublic:
    session_cookie = request.cookies.get("session_id")
    logger.bind(session_cookie=session_cookie).debug("Getting current user...")
    user = await user_service.get_user_by_session(session_id=session_cookie)
    logger.bind(session_cookie=session_cookie).debug("Got current user")
    return UserPublic.model_validate(asdict(user))


async def get_current_user_id(
    request: Request, user_service: UserService = Depends(get_user_service)
) -> UUID:
    session_cookie = request.cookies.get("session_id")
    logger.bind(session_cookie=session_cookie).debug("Getting current user id...")
    user_id = await user_service.get_user_id_by_session(session_id=session_cookie)
    logger.bind(session_cookie=session_cookie).debug("Got current user id")
    return user_id


async def get_current_session_id(
    request: Request, user_service: UserService = Depends(get_user_service)
) -> UUID:
    session_cookie = request.cookies.get("session_id")
    logger.bind(session_cookie=session_cookie).debug("Getting current session id...")
    session_id = await user_service.get_valid_session_id(session_id=session_cookie)
    logger.bind(session_cookie=session_cookie).debug("Got current session id")
    return session_id

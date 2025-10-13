from fastapi import Response

from app.core.constants import Environment
from app.core.settings import get_settings


def set_session_cookie(response: Response, session_id: str) -> None:
    is_production = get_settings().environment == Environment.PROD

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/api/users",
        max_age=get_settings().session_ttl_seconds,
    )

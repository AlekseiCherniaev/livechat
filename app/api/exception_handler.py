from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette import status

from app.domain.exceptions.analytics import RoomStatsNotFound, UserActivityNotFound
from app.domain.exceptions.join_request import (
    JoinRequestNotFound,
    JoinRequestAlreadyExists,
)
from app.domain.exceptions.message import (
    MessageNotFound,
    MessagePermissionError,
)
from app.domain.exceptions.notification import (
    NotificationNotFound,
    NotificationPermissionError,
)
from app.domain.exceptions.room import (
    RoomNotFound,
    RoomAlreadyExists,
    NoChangesDetected,
    RoomPermissionError,
)
from app.domain.exceptions.user import (
    UserAlreadyExists,
    UserNotFound,
    UserInvalidCredentials,
)
from app.domain.exceptions.user_session import (
    SessionNotFound,
    NoSessionCookie,
    InvalidSession,
)
from app.domain.exceptions.websocket_session import (
    WebSocketSessionNotFound,
    WebSocketSessionPermissionError,
)

EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    UserAlreadyExists: status.HTTP_400_BAD_REQUEST,
    UserNotFound: status.HTTP_404_NOT_FOUND,
    UserInvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    SessionNotFound: status.HTTP_404_NOT_FOUND,
    NoSessionCookie: status.HTTP_401_UNAUTHORIZED,
    InvalidSession: status.HTTP_401_UNAUTHORIZED,
    WebSocketSessionNotFound: status.HTTP_404_NOT_FOUND,
    WebSocketSessionPermissionError: status.HTTP_403_FORBIDDEN,
    RoomNotFound: status.HTTP_404_NOT_FOUND,
    RoomAlreadyExists: status.HTTP_400_BAD_REQUEST,
    NoChangesDetected: status.HTTP_400_BAD_REQUEST,
    RoomPermissionError: status.HTTP_400_BAD_REQUEST,
    JoinRequestNotFound: status.HTTP_404_NOT_FOUND,
    JoinRequestAlreadyExists: status.HTTP_400_BAD_REQUEST,
    NotificationNotFound: status.HTTP_404_NOT_FOUND,
    NotificationPermissionError: status.HTTP_403_FORBIDDEN,
    MessageNotFound: status.HTTP_404_NOT_FOUND,
    MessagePermissionError: status.HTTP_403_FORBIDDEN,
    RoomStatsNotFound: status.HTTP_404_NOT_FOUND,
    UserActivityNotFound: status.HTTP_404_NOT_FOUND,
}


def register_exception_handlers(app: FastAPI) -> None:
    for exc_class, exc_status in EXCEPTION_STATUS_MAP.items():

        @app.exception_handler(exc_class)
        async def handler(_: Request, exc: exc_class, http_status=exc_status):  # type: ignore
            return JSONResponse(
                status_code=http_status,
                content={"detail": str(exc)},
            )

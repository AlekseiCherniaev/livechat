from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette import status

from app.domain.exceptions.session import (
    SessionNotFound,
    NoSessionCookie,
    InvalidSession,
)
from app.domain.exceptions.user import (
    UserAlreadyExists,
    UserNotFound,
    UserInvalidCredentials,
)

EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    UserAlreadyExists: status.HTTP_400_BAD_REQUEST,
    UserNotFound: status.HTTP_404_NOT_FOUND,
    UserInvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    SessionNotFound: status.HTTP_404_NOT_FOUND,
    NoSessionCookie: status.HTTP_401_UNAUTHORIZED,
    InvalidSession: status.HTTP_401_UNAUTHORIZED,
}


def register_exception_handlers(app: FastAPI) -> None:
    for exc_class, exc_status in EXCEPTION_STATUS_MAP.items():

        @app.exception_handler(exc_class)
        async def handler(_: Request, exc: exc_class, http_status=exc_status):  # type: ignore
            return JSONResponse(
                status_code=http_status,
                content={"detail": str(exc)},
            )

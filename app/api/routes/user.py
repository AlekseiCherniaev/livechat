import structlog
from fastapi import APIRouter, Depends, Response, status, Request

from app.api.dependencies import set_session_cookie, get_current_user
from app.api.di import get_user_service
from app.api.schemas.user import UserCreate, UserPublic, UserLogin
from app.domain.services.user_service import UserService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register(
    user_data: UserCreate, service: UserService = Depends(get_user_service)
) -> Response:
    logger.bind(user_username=user_data.username).debug("Registering user...")
    await service.register_user(
        username=user_data.username, password=user_data.password
    )
    logger.bind(user_username=user_data.username).debug("Registered user")

    return Response(status_code=status.HTTP_200_OK)


@router.post("/login")
async def login(
    user_data: UserLogin,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> Response:
    logger.bind(username=user_data.username).debug("Logging in user...")
    session = await service.login_user(
        username=user_data.username, password=user_data.password
    )
    set_session_cookie(response=response, session_id=str(session.id))
    response.status_code = status.HTTP_200_OK
    logger.bind(username=user_data.username).debug("Logged in user")

    return response


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    service: UserService = Depends(get_user_service),
) -> Response:
    session_cookie = request.cookies.get("session_id")
    logger.bind(session_cookie=session_cookie).debug("Logging out user...")
    await service.logout_user(session_id=session_cookie)
    response.delete_cookie("session_id")
    response.status_code = status.HTTP_200_OK
    logger.bind(session_cookie=session_cookie).debug("Logged out user")

    return response


@router.get("/me")
async def me(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return user

import structlog
from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import get_current_user, set_session_cookie
from app.api.di import get_user_service
from app.api.schemas.user import UserAuth, UserPublic
from app.domain.dtos.user import UserAuthDTO
from app.domain.services.user import UserService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register-user")
async def register(
    user_data: UserAuth, user_service: UserService = Depends(get_user_service)
) -> Response:
    logger.bind(user_username=user_data.username).debug("Registering user...")
    user_dto = UserAuthDTO(username=user_data.username, password=user_data.password)
    await user_service.register_user(user_data=user_dto)
    logger.bind(user_username=user_data.username).debug("User registered")
    return Response(status_code=status.HTTP_200_OK)


@router.post("/login-user")
async def login(
    user_data: UserAuth,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> Response:
    logger.bind(username=user_data.username).debug("Logging in user...")
    user_dto = UserAuthDTO(username=user_data.username, password=user_data.password)
    session_id = await user_service.login_user(user_data=user_dto)
    set_session_cookie(response=response, session_id=str(session_id))
    response.status_code = status.HTTP_200_OK
    logger.bind(username=user_data.username).debug("User logged in")
    return response


@router.post("/logout-user")
async def logout(
    request: Request,
    response: Response,
    user_service: UserService = Depends(get_user_service),
) -> Response:
    session_cookie = request.cookies.get("session_id")
    logger.bind(session_cookie=session_cookie).debug("Logging out user...")
    await user_service.logout_user(session_id=session_cookie)
    response.delete_cookie("session_id")
    response.status_code = status.HTTP_200_OK
    logger.bind(session_cookie=session_cookie).debug("Logged out user")
    return response


@router.get("/get-me")
async def me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    return current_user

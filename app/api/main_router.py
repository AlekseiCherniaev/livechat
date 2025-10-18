from fastapi import APIRouter

from app.api.routes.user import router as user_router
from app.api.routes.status import router as status
from app.api.routes.notification import router as notification_router
from app.api.routes.message import router as message_router


def get_main_router() -> APIRouter:
    router = APIRouter(prefix="/api")
    router.include_router(status)
    router.include_router(user_router)
    router.include_router(notification_router)
    router.include_router(message_router)

    return router

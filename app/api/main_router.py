from fastapi import APIRouter

from app.api.routes.user import router as user_router


def get_main_router() -> APIRouter:
    router = APIRouter(prefix="/api")
    router.include_router(user_router)

    return router

import structlog
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.settings import get_settings

logger = structlog.getLogger(__name__)


def add_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=[f"*.{get_settings().domain}"]
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.debug("Middlewares added to the app")

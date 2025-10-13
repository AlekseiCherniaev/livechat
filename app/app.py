from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

import structlog
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from pymongo import AsyncMongoClient
from redis.asyncio import Redis
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from app.adapters.db.cassandra_engine import CassandraEngine
from app.adapters.db.mongo.indexes import ensure_indexes
from app.adapters.security.password_hasher import BcryptPasswordHasher
from app.api.exception_handler import register_exception_handlers
from app.api.main_router import get_main_router
from app.core.logger import prepare_logger
from app.core.settings import get_settings, Settings
from app.core.utils import use_handler_name_as_unique_id

logger = structlog.get_logger(__name__)


def get_app_config(settings: Settings) -> dict[Any, Any]:
    return dict(
        title=settings.project_name,
        description=settings.project_description,
        version=settings.project_version,
        docs_url=None,
        redoc_url=None,
        debug=settings.fast_api_debug,
        openapi_url="/api/internal/openapi.json",
        swagger_ui_oauth2_redirect_url="/api/internal/docs/oauth2-redirect",
        generate_unique_id_function=use_handler_name_as_unique_id,
        lifespan=lifespan,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    app.state.password_hasher = BcryptPasswordHasher()
    app.state.mongo_client = AsyncMongoClient(get_settings().mongo_uri)
    app.state.mongo_db = app.state.mongo_client[get_settings().mongo_dbname]
    await ensure_indexes(db=app.state.mongo_db)
    logger.info("MongoDB connected and indexes ensured")
    app.state.redis = Redis.from_url(
        get_settings().redis_dsn, encoding="utf-8", decode_responses=True
    )
    app.state.cassandra_engine = CassandraEngine()
    logger.info("Startup completed")
    yield
    await app.state.mongo_client.close()
    await app.state.redis.aclose()
    app.state.cassandra_engine.shutdown()
    logger.debug("Server stopped")


def init_app() -> FastAPI:
    prepare_logger(log_level=get_settings().log_level)

    logger.info("Initializing app")
    app = FastAPI(**get_app_config(get_settings()))
    app.mount(
        "/api/internal/static",
        StaticFiles(directory=f"{get_settings().static_url_path}"),
        name="static",
    )

    @app.get("/api/internal/docs", include_in_schema=False)
    async def custom_swagger_ui_html() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/api/internal/openapi.json",
            title="Livechat API",
            swagger_css_url="static/swagger-ui.css",
            swagger_js_url="static/swagger-ui-bundle.js",
            swagger_favicon_url="static/fastapi.png",
        )

    @app.get("/api/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(get_main_router())
    register_exception_handlers(app)

    return app

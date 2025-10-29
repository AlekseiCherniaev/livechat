from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from redis.asyncio import Redis
from starlette.staticfiles import StaticFiles

from app.adapters.analytics.clickhouse_client import create_clickhouse_client
from app.adapters.cache.memcache import MemcachedCache
from app.adapters.db.cassandra_engine import CassandraEngine
from app.adapters.db.mongo_client import create_mongo_client
from app.adapters.security.password_hasher import BcryptPasswordHasher
from app.api.exception_handler import register_exception_handlers
from app.api.main_router import get_main_router
from app.api.middlewares import add_middlewares
from app.core.logger import prepare_logger
from app.core.settings import Settings, get_settings
from app.core.utils import use_handler_name_as_unique_id

logger = structlog.get_logger(__name__)


def get_app_config(settings: Settings) -> dict[Any, Any]:
    return {
        "title": settings.project_name,
        "description": settings.project_description,
        "version": settings.project_version,
        "docs_url": None,
        "redoc_url": None,
        "debug": settings.fast_api_debug,
        "openapi_url": "/api/internal/openapi.json",
        "swagger_ui_oauth2_redirect_url": "/api/internal/docs/oauth2-redirect",
        "generate_unique_id_function": use_handler_name_as_unique_id,
        "lifespan": lifespan,
    }


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    app.state.bcrypt_password_hasher = BcryptPasswordHasher()
    app.state.mongo_client = await create_mongo_client()
    app.state.mongo_db = app.state.mongo_client[get_settings().mongo_dbname]
    app.state.redis = Redis.from_url(
        get_settings().redis_app_dsn, encoding="utf-8", decode_responses=True
    )
    app.state.memcache = MemcachedCache(
        host=get_settings().memcached_host, port=get_settings().memcached_port
    )
    app.state.cassandra_engine = CassandraEngine()
    app.state.clickhouse = await create_clickhouse_client()

    logger.info("Startup completed")
    yield
    await app.state.mongo_client.close()
    await app.state.redis.aclose()
    app.state.cassandra_engine.shutdown()
    await app.state.clickhouse.close()

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

    app.include_router(get_main_router())
    register_exception_handlers(app)
    add_middlewares(app)
    return app

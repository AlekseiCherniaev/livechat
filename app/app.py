from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

import structlog
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

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
    logger.info("Startup completed")
    yield
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

    return app

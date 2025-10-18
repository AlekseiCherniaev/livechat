from fastapi import APIRouter, Response, status
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse

router = APIRouter(tags=["status"])


@router.get("/internal/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="/api/internal/openapi.json",
        title="Livechat API",
        swagger_css_url="static/swagger-ui.css",
        swagger_js_url="static/swagger-ui-bundle.js",
        swagger_favicon_url="static/fastapi.png",
    )


@router.get("/health")
async def health_check() -> Response:
    return Response(status_code=status.HTTP_200_OK)

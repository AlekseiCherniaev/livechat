from uvicorn import run

from app.app import init_app
from app.core.settings import get_settings

if __name__ == "__main__":
    run(init_app(), host=get_settings().app_host, port=get_settings().app_port)

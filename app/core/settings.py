from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import Environment
from app.core.utils import get_project_config

base_dir = Path(__file__).parent.parent.parent

project_config = get_project_config(base_dir=base_dir)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=base_dir / ".env",
        env_file_encoding="utf-8",
    )

    project_name: str = project_config.get("name", "")
    project_version: str = project_config.get("version", "")
    project_description: str = project_config.get("description", "")
    static_url_path: Path = base_dir / "static"

    environment: Environment = Environment.TEST
    log_level: str = "DEBUG"
    fast_api_debug: bool = True

    app_host: str = "127.0.0.1"
    app_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()

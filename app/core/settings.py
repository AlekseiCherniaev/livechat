from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
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

    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_dbname: str = "chat_app"
    mongo_initdb_root_username: str = "root"
    mongo_initdb_root_password: str = "root-password"

    @computed_field  # type: ignore
    @property
    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@{self.mongo_host}:{self.mongo_port}?authSource=admin"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_app: int = 0
    redis_db_celery_broker: int = 1
    redis_db_celery_backend: int = 2
    user_session_ttl_seconds: int = 60 * 60
    web_socket_session_ttl_seconds: int = 30

    @computed_field  # type: ignore
    @property
    def redis_app_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    celery_redis_repair_lock_key: str = "outbox_repair_lock"
    celery_redis_repair_lock_key_timeout: int = 60 * 5
    celery_redis_worker_lock_key: str = "outbox_worker_lock"
    celery_redis_worker_lock_key_timeout: int = 60 * 5
    celery_schedule: float = 60.0

    @computed_field  # type: ignore
    @property
    def redis_celery_broker_dsn(self) -> str:
        return (
            f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db_celery_broker}"
        )

    @computed_field  # type: ignore
    @property
    def redis_celery_backend_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db_celery_backend}"

    cassandra_contact_point: str = "localhost"
    cassandra_port: int = 9042
    cassandra_keyspace: str = "messages"
    cassandra_user: str | None = None
    cassandra_password: str | None = None

    clickhouse_host: str = "localhost"
    clickhouse_tcp_port: int = 8123
    clickhouse_http_port: int = 9000
    clickhouse_user: str = "clickhouse"
    clickhouse_password: str = "clickhouse-password"
    clickhouse_db: str = "analytics"


@lru_cache
def get_settings() -> Settings:
    return Settings()

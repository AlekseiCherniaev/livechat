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
    domain: str = "localhost"  # "living-chat.online"
    domain_https: str = f"https://{domain}"
    domain_wss: str = f"wss://{domain}"

    @property
    def allowed_origins(self) -> list[str]:
        origins = [
            self.domain_https,
            self.domain_wss,
        ]
        if self.environment != Environment.PROD:
            origins.extend(
                [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                    "ws://localhost:5173",
                    "ws://127.0.0.1:5173",
                ]
            )
        return origins

    app_host: str = "127.0.0.1"
    app_port: int = 8000

    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_dbname: str = "chat_app"
    mongo_initdb_root_username: str = "root"
    mongo_initdb_root_password: str = ""

    @property
    def mongo_uri(self) -> str:
        if self.environment == Environment.TEST:
            return f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@{self.mongo_host}:{self.mongo_port}?authSource=admin"
        return f"mongodb://{self.mongo_initdb_root_username}:{self.mongo_initdb_root_password}@{self.mongo_host}:{self.mongo_port}?replicaSet=rs0&authSource=admin"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db_app: int = 0
    redis_db_celery_broker: int = 1
    redis_db_celery_backend: int = 2
    user_session_ttl_seconds: int = 60 * 60
    web_socket_session_ttl_seconds: int = 1800

    @property
    def redis_app_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db_app}"

    celery_redis_repair_lock_key: str = "outbox_repair_lock"
    celery_redis_repair_lock_key_timeout: int = 60 * 5
    celery_redis_worker_lock_key: str = "outbox_worker_lock"
    celery_redis_worker_lock_key_timeout: int = 60 * 5
    celery_schedule: float = 60.0

    @property
    def redis_celery_broker_dsn(self) -> str:
        return (
            f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db_celery_broker}"
        )

    @property
    def redis_celery_backend_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db_celery_backend}"

    memcached_host: str = "localhost"
    memcached_port: int = 11211
    user_cache_key_ttl: int = 60 * 60

    cassandra_contact_point: str = "localhost"
    cassandra_port: int = 9042
    cassandra_keyspace: str = "livechat"
    cassandra_user: str | None = None
    cassandra_password: str | None = None

    clickhouse_host: str = "localhost"
    clickhouse_tcp_port: int = 8123
    clickhouse_http_port: int = 9000
    clickhouse_user: str = "clickhouse"
    clickhouse_password: str = ""
    clickhouse_db: str = "analytics"


@lru_cache
def get_settings() -> Settings:
    return Settings()

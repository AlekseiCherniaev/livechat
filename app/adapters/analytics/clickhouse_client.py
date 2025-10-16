import clickhouse_connect
import structlog
from clickhouse_connect.driver.asyncclient import AsyncClient

from app.core.settings import get_settings

logger = structlog.get_logger(__name__)


async def ensure_database(client: AsyncClient, db_name: str) -> None:
    await client.command(f"CREATE DATABASE IF NOT EXISTS {db_name}")


async def ensure_tables(client: AsyncClient) -> None:
    await client.command("""
    CREATE TABLE IF NOT EXISTS analytics_events (
        id UUID,
        event_type String,
        user_id UUID,
        room_id UUID,
        timestamp DateTime64(3),
        payload String
    ) ENGINE = MergeTree()
    PARTITION BY toYYYYMM(timestamp)
    ORDER BY (room_id, timestamp)
    """)


async def create_clickhouse_client() -> AsyncClient:
    tmp_client = await clickhouse_connect.get_async_client(
        host=get_settings().clickhouse_host,
        port=get_settings().clickhouse_tcp_port,
        username=get_settings().clickhouse_user,
        password=get_settings().clickhouse_password,
        database="default",
    )
    await ensure_database(tmp_client, get_settings().clickhouse_db)
    await tmp_client.close()  # type: ignore

    client = await clickhouse_connect.get_async_client(
        host=get_settings().clickhouse_host,
        port=get_settings().clickhouse_tcp_port,
        username=get_settings().clickhouse_user,
        password=get_settings().clickhouse_password,
        database=get_settings().clickhouse_db,
    )
    await ensure_tables(client=client)
    logger.info("ClickHouse connected and table ensured")
    return client

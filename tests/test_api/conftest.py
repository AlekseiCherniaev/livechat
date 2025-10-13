from typing import AsyncGenerator

from asgi_lifespan import LifespanManager
from asgi_lifespan._types import ASGIApp
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from pymongo import AsyncMongoClient
from pytest_asyncio import fixture
from redis.asyncio import Redis
from starlette.datastructures import State
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from app.app import init_app
from app.core import settings as settings_module
from app.core.constants import Environment
from app.core.settings import Settings


@fixture(scope="session")
def mongo_container():
    with MongoDbContainer("mongo:7.0") as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(27017)
        yield {
            "host": host,
            "port": port,
            "username": container.username,
            "password": container.password,
        }


@fixture(scope="function")
async def mongo_client(mongo_container):
    client = AsyncMongoClient(mongo_container["uri"])
    yield client
    await client.close()


@fixture(scope="session")
def redis_container():
    with RedisContainer() as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)
        yield {"host": host, "port": port, "dsn": f"redis://{host}:{port}/0"}


@fixture(scope="function")
async def redis_client(redis_container):
    client = Redis.from_url(
        redis_container["dsn"], encoding="utf-8", decode_responses=True
    )
    yield client
    await client.aclose()


@fixture
def override_settings(redis_container, mongo_container, monkeypatch):
    test_settings = Settings(
        environment=Environment.TEST,
        mongo_host=mongo_container["host"],
        mongo_port=mongo_container["port"],
        mongo_initdb_root_username=mongo_container["username"],
        mongo_initdb_root_password=mongo_container["password"],
        redis_host=redis_container["host"],
        redis_port=redis_container["port"],
        redis_db=0,
    )
    monkeypatch.setattr(settings_module, "Settings", lambda: test_settings)


@fixture
def configured_app(override_settings) -> FastAPI:
    settings_module.get_settings.cache_clear()
    app = init_app()
    return app


@fixture
async def lifespan_manager(
    configured_app: FastAPI,
) -> AsyncGenerator[LifespanManager, None]:
    async with LifespanManager(configured_app) as m:
        yield m


@fixture
def lifespan_state(lifespan_manager: LifespanManager) -> State:
    return State(lifespan_manager._state)


@fixture
def initialized_app(lifespan_manager: LifespanManager) -> ASGIApp:
    return lifespan_manager.app


@fixture
async def async_client(initialized_app: ASGIApp) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=initialized_app), base_url="http://test"
    ) as c:
        yield c

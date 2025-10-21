from typing import Any

import structlog
from pymemcache import serde
from pymemcache.client import base

logger = structlog.get_logger(__name__)


class MemcachedCache:
    def __init__(self, host: str, port: int, default_ttl: int = 60):
        self.default_ttl = default_ttl
        self.client = base.Client(
            (host, port),
            serializer=serde.python_memcache_serializer,
            deserializer=serde.python_memcache_deserializer,
        )

    async def get(self, key: str) -> Any | None:
        try:
            result = self.client.get(key)
            if result:
                logger.bind(key=key).debug("Memcache hit")
            else:
                logger.bind(key=key).debug("Memcache miss")
            return result
        except Exception as e:
            logger.bind(e=str(e)).exception("Memcache get error")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if ttl is None:
            ttl = self.default_ttl
        try:
            self.client.set(key, value, expire=ttl)
            logger.bind(key=key).debug("Memcache set")
        except Exception as e:
            logger.bind(e=str(e)).warning("Memcache set error")
            return None

    async def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
            logger.bind(key=key).debug("Memcache delete")
        except Exception as e:
            logger.bind(e=str(e)).warning("Memcache delete error")
            return None

    async def exists(self, key: str) -> bool:
        try:
            result = self.client.get(key)
            return result is not None
        except Exception as e:
            logger.bind(e=str(e)).warning("Memcache exists error")
            return False

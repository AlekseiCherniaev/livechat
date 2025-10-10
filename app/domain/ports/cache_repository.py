from typing import Protocol, Any


class CachePort(Protocol):
    async def get(self, key: str) -> Any | None:
        pass

    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        pass

    async def delete(self, key: str) -> None:
        pass

    async def exists(self, key: str) -> bool:
        pass

    async def incr(self, key: str, amount: int = 1) -> int:
        pass

    async def clear_prefix(self, prefix: str) -> None:
        """Clear all keys that start with the given prefix."""
        pass

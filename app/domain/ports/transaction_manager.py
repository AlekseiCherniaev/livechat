from collections.abc import Callable
from typing import Any, Protocol


class TransactionManager(Protocol):
    async def run_in_transaction(self, func: Callable[..., Any]) -> Any: ...

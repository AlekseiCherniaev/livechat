from typing import Protocol, Callable, Any


class TransactionManager(Protocol):
    async def run_in_transaction(self, func: Callable[..., Any]) -> Any: ...

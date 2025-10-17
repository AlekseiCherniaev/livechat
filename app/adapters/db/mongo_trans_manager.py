from typing import Any, Callable, Awaitable

import structlog
from pymongo import AsyncMongoClient

logger = structlog.get_logger(__name__)


class MongoTransactionManager:
    def __init__(self, client: AsyncMongoClient[Any]) -> None:
        self._client = client

    async def run_in_transaction(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        async with self._client.start_session() as session:
            await session.start_transaction()
            try:
                logger.debug("Mongo transaction started")
                result = await func(db_session=session, *args, **kwargs)
                await session.commit_transaction()
                logger.debug("Mongo transaction committed")
                return result
            except Exception as e:
                logger.bind(e=str(e)).exception("Mongo transaction aborted")
                await session.abort_transaction()
                raise

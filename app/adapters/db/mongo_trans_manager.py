from typing import Any, Callable, Awaitable

import structlog
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

logger = structlog.get_logger(__name__)


class MongoTransactionManager:
    def __init__(self, client: AsyncMongoClient[Any], db: AsyncDatabase[Any]) -> None:
        self._client = client
        self._db = db

    async def run_in_transaction(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        async with self._client.start_session() as session:
            try:
                async with session.start_transaction():
                    logger.debug("Mongo transaction started")
                    result = await func(session=session, *args, **kwargs)
                    logger.debug("Mongo transaction committed")
                    return result
            except Exception as e:
                logger.bind(e=str(e)).exception("Mongo transaction aborted")
                raise

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.user import document_to_user, user_to_document
from app.domain.entities.user import User


class MongoUserRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["users"]

    async def save(
        self, user: User, db_session: AsyncClientSession | None = None
    ) -> User:
        doc = user_to_document(user=user)
        await self._col.replace_one(
            {"_id": doc["_id"]}, doc, upsert=True, session=db_session
        )
        return user

    async def get_by_id(
        self, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> User | None:
        doc = await self._col.find_one({"_id": str(user_id)}, session=db_session)
        return doc and document_to_user(doc=doc)

    async def get_by_username(
        self, username: str, db_session: AsyncClientSession | None = None
    ) -> User | None:
        doc = await self._col.find_one({"username": username}, session=db_session)
        return doc and document_to_user(doc=doc)

    async def update_last_active(
        self, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> None:
        now = datetime.now(timezone.utc)
        await self._col.update_one(
            {"_id": str(user_id)},
            {"$set": {"last_active_at": now, "updated_at": now}},
            session=db_session,
        )

    async def delete_by_id(
        self, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> None:
        await self._col.delete_one({"_id": str(user_id)}, session=db_session)

    async def exists(
        self, username: str, db_session: AsyncClientSession | None = None
    ) -> bool:
        doc = await self._col.find_one(
            {"username": username}, {"_id": 1}, session=db_session
        )
        return doc is not None

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.user import document_to_user, user_to_document
from app.domain.entities.user import User


class MongoUserRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["users"]

    async def save(self, user: User) -> User:
        doc = user_to_document(user=user)
        await self._col.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        doc = await self._col.find_one({"_id": str(user_id)})
        return document_to_user(doc=doc) if doc else None

    async def get_by_username(self, username: str) -> User | None:
        doc = await self._col.find_one({"username": username})
        return document_to_user(doc=doc) if doc else None

    async def update_last_active(self, user_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        await self._col.update_one(
            {"_id": str(user_id)}, {"$set": {"last_active_at": now, "updated_at": now}}
        )

    async def delete_by_id(self, user_id: UUID) -> None:
        await self._col.delete_one({"_id": str(user_id)})

    async def exists(self, username: str) -> bool:
        doc = await self._col.find_one({"username": username}, {"_id": 1})
        return doc is not None

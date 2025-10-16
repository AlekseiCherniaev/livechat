from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.notification import (
    document_to_notification,
    notification_to_document,
)
from app.domain.entities.notification import Notification


class MongoNotificationRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["notifications"]

    async def save(
        self, notification: Notification, db_session: Any | None = None
    ) -> Notification:
        doc = notification_to_document(notification)
        await self._col.replace_one(
            {"_id": doc["_id"]}, doc, upsert=True, session=db_session
        )
        return notification

    async def get_by_id(
        self, notification_id: UUID, db_session: Any | None = None
    ) -> Notification | None:
        doc = await self._col.find_one(
            {"_id": str(notification_id)}, session=db_session
        )
        return document_to_notification(doc) if doc else None

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool,
        limit: int,
        db_session: Any | None = None,
    ) -> list[Notification]:
        query: dict[str, Any] = {"user_id": str(user_id)}
        if unread_only:
            query["read"] = False
        cursor = (
            self._col.find(query, session=db_session)
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return [document_to_notification(doc) async for doc in cursor]

    async def delete_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None:
        await self._col.delete_many({"user_id": str(user_id)}, session=db_session)

    async def count_unread(self, user_id: UUID, db_session: Any | None = None) -> int:
        return await self._col.count_documents(
            {"user_id": str(user_id), "read": False}, session=db_session
        )

    async def mark_as_read(
        self, notification_id: UUID, db_session: Any | None = None
    ) -> None:
        await self._col.update_one(
            {"_id": str(notification_id)},
            {"$set": {"read": True, "updated_at": datetime.now(timezone.utc)}},
            session=db_session,
        )

    async def mark_all_as_read(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None:
        await self._col.update_many(
            {"user_id": str(user_id), "read": False},
            {"$set": {"read": True, "updated_at": datetime.now(timezone.utc)}},
            session=db_session,
        )

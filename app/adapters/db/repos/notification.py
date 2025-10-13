from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo_notification import (
    document_to_notification,
    notification_to_document,
)
from app.core.constants import NotificationType
from app.domain.entities.message import Message
from app.domain.entities.notification import Notification


class MongoNotificationRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["notifications"]

    async def create(self, notification: Notification) -> None:
        doc = notification_to_document(notification)
        await self._col.insert_one(doc)

    async def create_notifications_for_room(
        self, room_id: UUID, message: Message
    ) -> None:
        room = await self._col.database["chat_rooms"].find_one({"_id": str(room_id)})
        if not room or "participants" not in room:
            return
        participants = [
            UUID(uid) for uid in room["participants"] if UUID(uid) != message.user_id
        ]
        now = datetime.now(timezone.utc)
        notifications = [
            notification_to_document(
                Notification(
                    user_id=uid,
                    type=NotificationType.MESSAGE_SENT,
                    created_at=now,
                    payload={
                        "room_id": str(room_id),
                        "message_id": str(message.id),
                        "content": message.content,
                    },
                )
            )
            for uid in participants
        ]

        if notifications:
            await self._col.insert_many(notifications)

    async def get_user_notifications(
        self, user_id: UUID, unread_only: bool = False
    ) -> list[Notification]:
        query: dict[str, Any] = {"user_id": str(user_id)}
        if unread_only:
            query["read"] = False
        cursor = self._col.find(query).sort("created_at", ASCENDING)
        return [document_to_notification(doc) async for doc in cursor]

    async def mark_as_read(self, notification_id: UUID) -> None:
        await self._col.update_one(
            {"_id": str(notification_id)}, {"$set": {"read": True}}
        )

    async def delete_by_user(self, user_id: UUID) -> None:
        await self._col.delete_many({"user_id": str(user_id)})

    async def count_unread(self, user_id: UUID) -> int:
        return await self._col.count_documents({"user_id": str(user_id), "read": False})

    async def mark_all_as_read(self, user_id: UUID) -> None:
        await self._col.update_many(
            {"user_id": str(user_id)},
            {"$set": {"read": True, "updated_at": datetime.now(timezone.utc)}},
        )

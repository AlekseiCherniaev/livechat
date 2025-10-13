from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo_chat import (
    chat_room_to_document,
    document_to_chat_room,
)
from app.domain.entities.chat_room import ChatRoom


class MongoChatRoom:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["chat_rooms"]

    async def save(self, room: ChatRoom) -> ChatRoom:
        doc = chat_room_to_document(room)
        await self._col.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return room

    async def get(self, room_id: UUID) -> ChatRoom | None:
        doc = await self._col.find_one({"_id": str(room_id)})
        return document_to_chat_room(doc) if doc else None

    async def update(self, room: ChatRoom) -> None:
        room.updated_at = datetime.now(timezone.utc)
        await self._col.update_one(
            {"_id": str(room.id)},
            {"$set": chat_room_to_document(room)},
        )

    async def delete_by_id(self, room_id: UUID) -> None:
        await self._col.delete_one({"_id": str(room_id)})

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ChatRoom]:
        cursor = (
            self._col.find().sort("created_at", ASCENDING).skip(offset).limit(limit)
        )
        return [document_to_chat_room(doc) async for doc in cursor]

    async def list_by_user(self, user_id: UUID) -> list[ChatRoom]:
        cursor = self._col.find({"participants": str(user_id)})
        return [document_to_chat_room(doc) async for doc in cursor]

    async def add_participant(self, room_id: UUID, user_id: UUID) -> None:
        await self._col.update_one(
            {"_id": str(room_id)},
            {
                "$addToSet": {"participants": str(user_id)},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    async def remove_participant(self, room_id: UUID, user_id: UUID) -> None:
        await self._col.update_one(
            {"_id": str(room_id)},
            {
                "$pull": {"participants": str(user_id)},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    async def exists(self, name: str) -> bool:
        doc = await self._col.find_one({"name": name}, {"_id": 1})
        return doc is not None

    async def count_participants(self, room_id: UUID) -> int:
        doc = await self._col.find_one({"_id": str(room_id)}, {"participants": 1})
        return len(doc.get("participants", [])) if doc else 0

    async def find_most_active_rooms(self, limit: int = 10) -> list[ChatRoom]:
        cursor = self._col.find().sort("updated_at", -1).limit(limit)
        return [document_to_chat_room(doc) async for doc in cursor]

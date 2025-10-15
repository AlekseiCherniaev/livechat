from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.room import (
    room_to_document,
    document_to_room,
)
from app.domain.entities.room import Room


class MongoRoomRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["rooms"]

    async def save(self, room: Room) -> Room:
        doc = room_to_document(room)
        await self._col.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return room

    async def get_by_id(self, room_id: UUID) -> Room | None:
        doc = await self._col.find_one({"_id": str(room_id)})
        return document_to_room(doc) if doc else None

    async def search(self, query: str, limit: int) -> list[Room]:
        regex = {"$regex": query, "$options": "i"}
        cursor = (
            self._col.find({"$or": [{"name": regex}, {"description": regex}]})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return [document_to_room(doc) async for doc in cursor]

    async def delete_by_id(self, room_id: UUID) -> None:
        await self._col.delete_one({"_id": str(room_id)})

    async def list_top_room(self, limit: int, only_public: bool) -> list[Room]:
        query: dict[str, Any] = {}
        if only_public:
            query["is_public"] = True

        cursor = (
            self._col.find(query).sort("participants_count", DESCENDING).limit(limit)
        )
        return [document_to_room(doc) async for doc in cursor]

    async def add_participant(self, room_id: UUID) -> None:
        await self._col.update_one(
            {"_id": str(room_id)},
            {
                "$inc": {"participants_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    async def remove_participant(self, room_id: UUID) -> None:
        await self._col.update_one(
            {"_id": str(room_id)},
            [
                {
                    "$set": {
                        "participants_count": {
                            "$max": [{"$subtract": ["$participants_count", 1]}, 0]
                        },
                        "updated_at": datetime.now(timezone.utc),
                    }
                }
            ],
        )

    async def exists(self, name: str) -> bool:
        doc = await self._col.find_one({"name": name}, {"_id": 1})
        return doc is not None

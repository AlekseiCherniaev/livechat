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

    async def save(self, room: Room, db_session: Any | None = None) -> Room:
        doc = room_to_document(room)
        await self._col.replace_one(
            {"_id": doc["_id"]}, doc, upsert=True, session=db_session
        )
        return room

    async def get_by_id(
        self, room_id: UUID, db_session: Any | None = None
    ) -> Room | None:
        doc = await self._col.find_one({"_id": str(room_id)}, session=db_session)
        return document_to_room(doc) if doc else None

    async def search(
        self, query: str, limit: int, db_session: Any | None = None
    ) -> list[Room]:
        regex = {"$regex": query, "$options": "i"}
        cursor = (
            self._col.find(
                {"$or": [{"name": regex}, {"description": regex}]}, session=db_session
            )
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        return [document_to_room(doc) async for doc in cursor]

    async def delete_by_id(self, room_id: UUID, db_session: Any | None = None) -> None:
        await self._col.delete_one({"_id": str(room_id)}, session=db_session)

    async def list_top_room(
        self, limit: int, only_public: bool, db_session: Any | None = None
    ) -> list[Room]:
        query: dict[str, Any] = {}
        if only_public:
            query["is_public"] = True

        cursor = (
            self._col.find(query, session=db_session)
            .sort("participants_count", DESCENDING)
            .limit(limit)
        )
        return [document_to_room(doc) async for doc in cursor]

    async def add_participant(
        self, room_id: UUID, db_session: Any | None = None
    ) -> None:
        await self._col.update_one(
            {"_id": str(room_id)},
            {
                "$inc": {"participants_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            session=db_session,
        )

    async def remove_participant(
        self, room_id: UUID, db_session: Any | None = None
    ) -> None:
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
            session=db_session,
        )

    async def exists(self, name: str, db_session: Any | None = None) -> bool:
        doc = await self._col.find_one({"name": name}, session=db_session)
        return doc is not None

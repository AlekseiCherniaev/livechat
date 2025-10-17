from typing import Any, Mapping, Sequence
from uuid import UUID

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.room import document_to_room
from app.adapters.db.models.mongo.room_membership import (
    room_membership_to_document,
)
from app.adapters.db.models.mongo.user import document_to_user
from app.domain.entities.room import Room
from app.domain.entities.room_membership import RoomMembership
from app.domain.entities.user import User


class MongoRoomMembershipRepository:
    def __init__(self, db: AsyncDatabase[Any]):
        self._col = db["room_memberships"]
        self._col_users = db["users"]
        self._col_rooms = db["rooms"]

    async def save(
        self,
        room_membership: RoomMembership,
        db_session: AsyncClientSession | None = None,
    ) -> RoomMembership:
        doc = room_membership_to_document(room_membership)
        await self._col.replace_one(
            {"room_id": doc["room_id"], "user_id": doc["user_id"]},
            doc,
            upsert=True,
            session=db_session,
        )
        return room_membership

    async def delete(
        self, room_id: UUID, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> None:
        await self._col.delete_one(
            {"room_id": str(room_id), "user_id": str(user_id)}, session=db_session
        )

    async def list_users(
        self, room_id: UUID, db_session: AsyncClientSession | None = None
    ) -> list[User]:
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$match": {"room_id": str(room_id)}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info",
                }
            },
            {"$unwind": "$user_info"},
        ]
        cursor = await self._col.aggregate(pipeline, session=db_session)

        return [document_to_user(doc["user_info"]) async for doc in cursor]

    async def list_rooms_for_user(
        self, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> list[Room]:
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$match": {"user_id": str(user_id)}},
            {
                "$lookup": {
                    "from": "rooms",
                    "localField": "room_id",
                    "foreignField": "_id",
                    "as": "room_info",
                }
            },
            {"$unwind": "$room_info"},
        ]
        cursor = await self._col.aggregate(pipeline, session=db_session)

        return [document_to_room(doc["room_info"]) async for doc in cursor]

    async def exists(
        self, room_id: UUID, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> bool:
        doc = await self._col.find_one(
            {"room_id": str(room_id), "user_id": str(user_id)},
            {"_id": 1},
            session=db_session,
        )
        return doc is not None

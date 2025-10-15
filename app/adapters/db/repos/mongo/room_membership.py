from typing import Any
from uuid import UUID

from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.room_membership import (
    room_membership_to_document,
)
from app.domain.dtos.room import RoomPublicDTO, room_to_dto
from app.domain.dtos.user import UserPublicDTO, user_to_dto
from app.domain.entities.room import Room
from app.domain.entities.room_membership import RoomMembership
from app.domain.entities.user import User


class MongoRoomMembershipRepository:
    def __init__(self, db: AsyncDatabase[Any]):
        self._col = db["room_memberships"]
        self._col_users = db["users"]
        self._col_rooms = db["rooms"]

    async def save(self, room_membership: RoomMembership) -> RoomMembership:
        doc = room_membership_to_document(room_membership)
        await self._col.replace_one(
            {"room_id": doc["room_id"], "user_id": doc["user_id"]}, doc, upsert=True
        )
        return room_membership

    async def delete(self, room_id: UUID, user_id: UUID) -> None:
        await self._col.delete_one({"room_id": str(room_id), "user_id": str(user_id)})

    async def list_users(self, room_id: UUID) -> list[UserPublicDTO]:
        pipeline = [
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
        cursor = await self._col.aggregate(pipeline)
        result = []
        async for doc in cursor:
            user_doc = doc["user_info"]
            result.append(
                user_to_dto(
                    User(
                        id=UUID(user_doc["_id"]),
                        username=user_doc["username"],
                        hashed_password=user_doc.get("hashed_password"),
                        created_at=user_doc.get("created_at"),
                        updated_at=user_doc.get("updated_at"),
                        last_login_at=user_doc.get("last_login_at"),
                        last_active=user_doc.get("last_active"),
                    )
                )
            )
        return result

    async def list_rooms_for_user(self, user_id: UUID) -> list[RoomPublicDTO]:
        pipeline = [
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
        cursor = await self._col.aggregate(pipeline)
        result = []
        async for doc in cursor:
            room_doc = doc["room_info"]
            result.append(
                room_to_dto(
                    Room(
                        id=UUID(room_doc["_id"]),
                        name=room_doc["name"],
                        description=room_doc.get("description"),
                        is_public=room_doc["is_public"],
                        participants_count=room_doc.get("participants_count", 0),
                        created_by=UUID(room_doc["created_by"]),
                        created_at=room_doc.get("created_at"),
                        updated_at=room_doc.get("updated_at"),
                    )
                )
            )
        return result

    async def exists(self, room_id: UUID, user_id: UUID) -> bool:
        doc = await self._col.find_one(
            {"room_id": str(room_id), "user_id": str(user_id)}, {"_id": 1}
        )
        return doc is not None

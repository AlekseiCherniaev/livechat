from typing import Any, Sequence, Mapping
from uuid import UUID

from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.join_request import (
    join_request_to_document,
    document_to_join_request,
)
from app.adapters.db.models.mongo.room import document_to_room
from app.adapters.db.models.mongo.user import document_to_user
from app.core.constants import JoinRequestStatus
from app.domain.entities.join_request import JoinRequest
from app.domain.entities.room import Room
from app.domain.entities.user import User


class MongoJoinRequestRepository:
    def __init__(self, db: AsyncDatabase[Any]):
        self._col = db["join_requests"]
        self._col_users = db["users"]
        self._col_rooms = db["rooms"]

    async def save(
        self, request: JoinRequest, db_session: AsyncClientSession | None = None
    ) -> JoinRequest:
        doc = join_request_to_document(request)
        await self._col.replace_one(
            {"_id": doc["_id"]}, doc, upsert=True, session=db_session
        )
        return request

    async def get_by_id(
        self, request_id: UUID, db_session: AsyncClientSession | None = None
    ) -> JoinRequest | None:
        doc = await self._col.find_one({"_id": str(request_id)}, session=db_session)
        return doc and document_to_join_request(doc)

    async def delete_by_id(
        self, request_id: UUID, db_session: AsyncClientSession | None = None
    ) -> None:
        await self._col.delete_one({"_id": str(request_id)}, session=db_session)

    async def list_by_room(
        self,
        room_id: UUID,
        status: JoinRequestStatus,
        db_session: AsyncClientSession | None = None,
    ) -> list[tuple[JoinRequest, User, Room]]:
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$match": {"room_id": str(room_id), "status": status.value}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info",
                }
            },
            {"$unwind": "$user_info"},
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

        return [
            (
                document_to_join_request(doc),
                document_to_user(doc["user_info"]),
                document_to_room(doc["room_info"]),
            )
            async for doc in cursor
        ]

    async def list_by_user(
        self,
        user_id: UUID,
        status: JoinRequestStatus,
        db_session: AsyncClientSession | None = None,
    ) -> list[tuple[JoinRequest, User, Room]]:
        pipeline: Sequence[Mapping[str, Any]] = [
            {"$match": {"user_id": str(user_id), "status": status.value}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info",
                }
            },
            {"$unwind": "$user_info"},
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
        return [
            (
                document_to_join_request(doc),
                document_to_user(doc["user_info"]),
                document_to_room(doc["room_info"]),
            )
            async for doc in cursor
        ]

    async def exists(
        self, room_id: UUID, user_id: UUID, db_session: AsyncClientSession | None = None
    ) -> bool:
        doc = await self._col.find_one(
            {"room_id": str(room_id), "user_id": str(user_id)},
            {"_id": 1},
            session=db_session,
        )
        return doc is not None

from datetime import datetime
from typing import Any
from uuid import UUID

from pymongo import ASCENDING
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.outbox import outbox_to_document, document_to_outbox
from app.core.constants import OutboxStatus
from app.domain.entities.outbox import Outbox


class MongoOutboxRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["outboxes"]

    async def save(
        self, outbox: Outbox, db_session: AsyncClientSession | None = None
    ) -> Outbox:
        doc = outbox_to_document(outbox)
        await self._col.update_one(
            {"dedup_key": outbox.dedup_key},
            {"$setOnInsert": doc},
            upsert=True,
            session=db_session,
        )
        return outbox

    async def get_by_id(
        self, outbox_id: UUID, db_session: AsyncClientSession | None = None
    ) -> Outbox | None:
        doc = await self._col.find_one({"_id": str(outbox_id)}, session=db_session)
        return document_to_outbox(doc) if doc else None

    async def list_pending(
        self, limit: int, db_session: AsyncClientSession | None = None
    ) -> list[Outbox]:
        cursor = (
            self._col.find({"status": OutboxStatus.PENDING.value}, session=db_session)
            .sort("created_at", ASCENDING)
            .limit(limit)
        )
        return [document_to_outbox(doc) async for doc in cursor]

    async def mark_in_progress(
        self, outbox_id: UUID, db_session: AsyncClientSession | None = None
    ) -> None:
        await self._col.update_one(
            {
                "_id": str(outbox_id),
                "status": OutboxStatus.PENDING.value,
            },
            {
                "$set": {
                    "status": OutboxStatus.IN_PROGRESS.value,
                }
            },
            session=db_session,
        )

    async def mark_sent(
        self,
        outbox_id: UUID,
        sent_at: datetime,
        db_session: AsyncClientSession | None = None,
    ) -> None:
        await self._col.update_one(
            {"_id": str(outbox_id)},
            {
                "$set": {
                    "status": OutboxStatus.SENT.value,
                    "sent": True,
                    "sent_at": sent_at,
                }
            },
            session=db_session,
        )

    async def mark_failed(
        self, outbox_id: UUID, error: str, db_session: AsyncClientSession | None = None
    ) -> None:
        await self._col.update_one(
            {"_id": str(outbox_id)},
            {
                "$set": {
                    "status": OutboxStatus.FAILED.value,
                    "last_error": error,
                },
                "$inc": {"retries": 1},
            },
            session=db_session,
        )

    async def delete_by_id(
        self, outbox_id: UUID, db_session: AsyncClientSession | None = None
    ) -> None:
        await self._col.delete_one({"_id": str(outbox_id)}, session=db_session)

    async def exists_by_dedup_keys(
        self, dedup_keys: list[str], db_session: AsyncClientSession | None = None
    ) -> list[str]:
        cursor = self._col.find(
            {"dedup_key": {"$in": dedup_keys}},
            {"dedup_key": 1, "_id": 0},
            session=db_session,
        )
        existing = [doc["dedup_key"] async for doc in cursor]
        return existing

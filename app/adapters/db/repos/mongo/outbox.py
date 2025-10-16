from datetime import datetime
from typing import Any
from uuid import UUID

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.adapters.db.models.mongo.outbox import outbox_to_document, document_to_outbox
from app.core.constants import OutboxStatus
from app.domain.entities.outbox import Outbox


class MongoOutboxRepository:
    def __init__(self, db: AsyncDatabase[Any]) -> None:
        self._col = db["outboxes"]

    async def save(self, outbox: Outbox) -> Outbox:
        doc = outbox_to_document(outbox)
        await self._col.replace_one({"_id": doc["_id"]}, doc, upsert=True)
        return outbox

    async def get_by_id(self, outbox_id: UUID) -> Outbox | None:
        doc = await self._col.find_one({"_id": str(outbox_id)})
        return document_to_outbox(doc) if doc else None

    async def list_pending(self, limit: int = 100) -> list[Outbox]:
        cursor = (
            self._col.find({"status": OutboxStatus.PENDING.value})
            .sort("created_at", ASCENDING)
            .limit(limit)
        )
        return [document_to_outbox(doc) async for doc in cursor]

    async def mark_in_progress(self, outbox_id: UUID) -> None:
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
        )

    async def mark_sent(self, outbox_id: UUID, sent_at: datetime) -> None:
        await self._col.update_one(
            {"_id": str(outbox_id)},
            {
                "$set": {
                    "status": OutboxStatus.SENT.value,
                    "sent": True,
                    "sent_at": sent_at,
                }
            },
        )

    async def mark_failed(self, outbox_id: UUID, error: str) -> None:
        await self._col.update_one(
            {"_id": str(outbox_id)},
            {
                "$set": {
                    "status": OutboxStatus.FAILED.value,
                    "last_error": error,
                },
                "$inc": {"retries": 1},
            },
        )

    async def delete_by_id(self, outbox_id: UUID) -> None:
        await self._col.delete_one({"_id": str(outbox_id)})

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

from app.adapters.db.models.cassandra.message import (
    MessageModel,
    MessageByUserModel,
    MessageByIdModel,
    MessageGlobalModel,
)
from app.domain.entities.message import Message


class CassandraMessageRepository:
    async def save(self, message: Message, db_session: Any | None = None) -> None:
        def _save() -> None:
            MessageModel.from_entity(message).save()
            MessageByUserModel.from_entity(message).save()
            MessageByIdModel.from_entity(message).save()
            MessageGlobalModel.from_entity(message).save()

        await asyncio.to_thread(_save)

    async def get_recent_by_room(
        self, room_id: UUID, limit: int, db_session: Any | None = None
    ) -> list[Message]:
        def _get() -> list[Message]:
            return [
                msg.to_entity()
                for msg in MessageModel.objects(room_id=room_id).limit(limit)
            ]

        return await asyncio.to_thread(_get)

    async def get_by_id(
        self, message_id: UUID, db_session: Any | None = None
    ) -> Message | None:
        def _get() -> Message | None:
            msg: MessageByIdModel | None = MessageByIdModel.objects(
                id=message_id
            ).first()
            return msg and msg.to_entity()

        return await asyncio.to_thread(_get)

    async def get_since_all_rooms(
        self,
        since: datetime,
        limit: int,
        start_after: tuple[datetime, UUID] | None = None,
        db_session: Any | None = None,
    ) -> list[Message]:
        def _get() -> list[Message]:
            query = MessageGlobalModel.objects(partition="all", created_at__gte=since)
            if start_after:
                last_created, last_id = start_after
                query = query.filter(
                    (MessageGlobalModel.created_at < last_created)
                    | (
                        (MessageGlobalModel.created_at == last_created)
                        & (MessageGlobalModel.id < last_id)
                    )
                )
            query = query.limit(limit)
            return [msg.to_entity() for msg in query.all()]

        return await asyncio.to_thread(_get)

    async def delete_by_id(
        self, message_id: UUID, db_session: Any | None = None
    ) -> None:
        def _delete() -> None:
            msg_by_id = MessageByIdModel.objects(id=message_id).first()
            if not msg_by_id:
                return

            msg_main = MessageModel.objects(
                room_id=msg_by_id.room_id, created_at=msg_by_id.created_at
            ).first()
            if msg_main:
                msg_main.delete()

            msg_user = MessageByUserModel.objects(
                user_id=msg_by_id.user_id, created_at=msg_by_id.created_at
            ).first()
            if msg_user:
                msg_user.delete()

            msg_global = MessageGlobalModel.objects(
                partition="all", created_at=msg_by_id.created_at, id=msg_by_id.id
            ).first()
            if msg_global:
                msg_global.delete()

            msg_by_id.delete()

        await asyncio.to_thread(_delete)

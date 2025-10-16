import asyncio
from typing import Any
from uuid import UUID

from app.adapters.db.models.cassandra.message import (
    MessageModel,
    MessageByUserModel,
    MessageByIdModel,
)
from app.domain.entities.message import Message


class CassandraMessageRepository:
    async def save(self, message: Message, db_session: Any | None = None) -> None:
        def _save() -> None:
            MessageModel.from_entity(message).save()
            MessageByUserModel.from_entity(message).save()
            MessageByIdModel.from_entity(message).save()

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
            msg = MessageByIdModel.objects(id=message_id).first()
            return msg.to_entity() if msg else None

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

            msg_by_id.delete()

        await asyncio.to_thread(_delete)

    async def list_by_user(
        self, user_id: UUID, limit: int, db_session: Any | None = None
    ) -> list[Message]:
        def _list() -> list[Message]:
            return [
                msg.to_entity()
                for msg in MessageByUserModel.objects(user_id=user_id).limit(limit)
            ]

        return await asyncio.to_thread(_list)

from datetime import UTC, datetime
from uuid import uuid4

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

from app.core.settings import get_settings
from app.domain.entities.message import Message


class MessageModel(Model):  # type: ignore[misc]
    __keyspace__ = get_settings().cassandra_keyspace
    __table_name__ = "messages"

    room_id = columns.UUID(primary_key=True, partition_key=True)
    created_at = columns.DateTime(primary_key=True, clustering_order="DESC")

    user_id = columns.UUID()
    content = columns.Text()
    edited = columns.Boolean(default=False)
    updated_at = columns.DateTime(default=lambda: datetime.now(UTC))
    id = columns.UUID(default=uuid4)

    def to_entity(self) -> Message:
        return Message(
            id=self.id,
            room_id=self.room_id,
            user_id=self.user_id,
            content=self.content,
            edited=self.edited,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageModel":
        return cls(
            id=entity.id,
            room_id=entity.room_id,
            user_id=entity.user_id,
            content=entity.content,
            edited=entity.edited,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class MessageByUserModel(Model):  # type: ignore[misc]
    __keyspace__ = get_settings().cassandra_keyspace
    __table_name__ = "messages_by_user"

    user_id = columns.UUID(primary_key=True, partition_key=True)
    created_at = columns.DateTime(primary_key=True, clustering_order="DESC")

    message_id = columns.UUID(default=uuid4)
    room_id = columns.UUID()
    content = columns.Text()
    edited = columns.Boolean(default=False)
    updated_at = columns.DateTime(default=lambda: datetime.now(UTC))

    def to_entity(self) -> Message:
        return Message(
            id=self.message_id,
            room_id=self.room_id,
            user_id=self.user_id,
            content=self.content,
            edited=self.edited,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageByUserModel":
        return cls(
            message_id=entity.id,
            room_id=entity.room_id,
            user_id=entity.user_id,
            content=entity.content,
            edited=entity.edited,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class MessageByIdModel(Model):  # type: ignore[misc]
    __keyspace__ = get_settings().cassandra_keyspace
    __table_name__ = "messages_by_id"

    id = columns.UUID(primary_key=True, default=uuid4)
    room_id = columns.UUID()
    user_id = columns.UUID()
    content = columns.Text()
    created_at = columns.DateTime()
    edited = columns.Boolean(default=False)
    updated_at = columns.DateTime(default=lambda: datetime.now(UTC))

    def to_entity(self) -> Message:
        return Message(
            id=self.id,
            room_id=self.room_id,
            user_id=self.user_id,
            content=self.content,
            edited=self.edited,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageByIdModel":
        return cls(
            id=entity.id,
            room_id=entity.room_id,
            user_id=entity.user_id,
            content=entity.content,
            edited=entity.edited,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class MessageGlobalModel(Model):  # type: ignore[misc]
    __keyspace__ = get_settings().cassandra_keyspace
    __table_name__ = "messages_global"

    partition = columns.Text(primary_key=True, partition_key=True, default="all")
    created_at = columns.DateTime(primary_key=True, clustering_order="DESC")
    id = columns.UUID(primary_key=True, clustering_order="DESC", default=uuid4)

    room_id = columns.UUID()
    user_id = columns.UUID()
    content = columns.Text()
    edited = columns.Boolean(default=False)
    updated_at = columns.DateTime(default=lambda: datetime.now(UTC))

    def to_entity(self) -> Message:
        return Message(
            id=self.id,
            room_id=self.room_id,
            user_id=self.user_id,
            content=self.content,
            edited=self.edited,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_entity(cls, entity: Message) -> "MessageGlobalModel":
        return cls(
            created_at=entity.created_at,
            id=entity.id,
            room_id=entity.room_id,
            user_id=entity.user_id,
            content=entity.content,
            edited=entity.edited,
            updated_at=entity.updated_at,
        )

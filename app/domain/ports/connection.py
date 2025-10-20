from typing import Protocol
from uuid import UUID

from app.core.constants import BroadcastEventType
from app.domain.entities.event_payload import EventPayload


class ConnectionPort(Protocol):
    async def connect_user_to_room(self, user_id: UUID, room_id: UUID) -> None: ...

    async def disconnect_user(self, user_id: UUID) -> None: ...

    async def disconnect_user_from_room(self, user_id: UUID, room_id: UUID) -> None: ...

    async def get_user_connections(self, user_id: UUID) -> set[UUID]: ...

    async def broadcast_event(
        self, room_id: UUID, event_type: BroadcastEventType, event_payload: EventPayload
    ) -> None: ...

    async def send_event_to_user(
        self, user_id: UUID, event_type: BroadcastEventType, event_payload: EventPayload
    ) -> None: ...

    async def list_active_user_ids_in_room(self, room_id: UUID) -> list[UUID]: ...

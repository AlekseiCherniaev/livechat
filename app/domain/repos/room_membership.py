from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.room import Room
from app.domain.entities.room_membership import RoomMembership
from app.domain.entities.user import User


class RoomMembershipRepository(Protocol):
    async def save(
        self, room_membership: RoomMembership, db_session: Any | None = None
    ) -> RoomMembership: ...

    async def delete(
        self, room_id: UUID, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def delete_by_room(
        self, room_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def list_users(
        self, room_id: UUID, db_session: Any | None = None
    ) -> list[User]: ...

    async def list_rooms_for_user(
        self, user_id: UUID, db_session: Any | None = None
    ) -> list[Room]: ...

    async def exists(
        self, room_id: UUID, user_id: UUID, db_session: Any | None = None
    ) -> bool: ...

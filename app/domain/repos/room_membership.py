from typing import Protocol
from uuid import UUID

from app.domain.entities.room import Room
from app.domain.entities.room_membership import RoomMembership
from app.domain.entities.user import User


class RoomMembershipRepository(Protocol):
    async def save(self, room_membership: RoomMembership) -> RoomMembership: ...

    async def delete(self, room_id: UUID, user_id: UUID) -> None: ...

    async def list_users(self, room_id: UUID) -> list[User]: ...

    async def list_rooms_for_user(self, user_id: UUID) -> list[Room]: ...

    async def exists(self, room_id: UUID, user_id: UUID) -> bool: ...

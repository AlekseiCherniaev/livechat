from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.join_request import JoinRequest
from app.domain.entities.room import Room
from app.domain.entities.user import User


class JoinRequestRepository(Protocol):
    async def save(
        self, request: JoinRequest, db_session: Any | None = None
    ) -> JoinRequest: ...

    async def get_by_id(
        self, request_id: UUID, db_session: Any | None = None
    ) -> JoinRequest | None: ...

    async def delete_by_id(
        self, request_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def list_by_room(
        self, room_id: UUID, db_session: Any | None = None
    ) -> list[tuple[JoinRequest, User, Room]]: ...

    async def list_by_user(
        self, user_id: UUID, db_session: Any | None = None
    ) -> list[tuple[JoinRequest, User, Room]]: ...

    async def exists(
        self, room_id: UUID, user_id: UUID, db_session: Any | None = None
    ) -> bool: ...

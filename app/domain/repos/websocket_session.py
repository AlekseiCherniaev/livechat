from typing import Protocol, Any
from uuid import UUID

from app.domain.entities.websocket_session import WebSocketSession


class WebSocketSessionRepository(Protocol):
    async def save(
        self, session: WebSocketSession, db_session: Any | None = None
    ) -> None: ...

    async def get_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> WebSocketSession | None: ...

    async def list_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> list[WebSocketSession]: ...

    async def delete_by_id(
        self, session_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def delete_by_user_id(
        self, user_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def update_last_ping(
        self, session_id: UUID, db_session: Any | None = None
    ) -> None: ...

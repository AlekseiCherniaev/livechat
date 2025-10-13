from typing import Protocol
from uuid import UUID
from app.domain.entities.websocket_session import WebSocketSession


class WebSocketSessionRepository(Protocol):
    async def save(self, session: WebSocketSession) -> None:
        pass

    async def get(self, session_id: UUID) -> WebSocketSession | None:
        pass

    async def list_by_user_id(self, user_id: UUID) -> list[WebSocketSession]:
        pass

    async def delete_by_id(self, session_id: UUID) -> None:
        pass

    async def delete_by_user_id(self, user_id: UUID) -> None:
        pass

    async def is_online(self, user_id: UUID) -> bool:
        pass

from typing import Protocol
from app.domain.entities.websocket_session import WebSocketSession


class ConnectionPort(Protocol):
    async def connect(self, session: WebSocketSession) -> None:
        pass

    async def disconnect(self, session_id: str) -> None:
        pass

    async def update_ping(self, session_id: str) -> None:
        pass

    async def get_active_sessions(self, room_id: str) -> list[WebSocketSession]:
        pass

    async def is_user_online(self, user_id: str) -> bool:
        pass

    async def get_rooms_for_user(self, user_id: str) -> list[str]:
        pass

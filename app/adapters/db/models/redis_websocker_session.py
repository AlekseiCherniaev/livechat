from typing import Any
from uuid import UUID
from datetime import datetime
from app.domain.entities.websocket_session import WebSocketSession


def session_to_dict(session: WebSocketSession) -> dict[str, Any]:
    return {
        "id": str(session.id),
        "user_id": str(session.user_id),
        "room_id": str(session.room_id),
        "connected_at": session.connected_at.isoformat(),
        "last_ping_at": session.last_ping_at.isoformat(),
        "disconnected_at": session.disconnected_at.isoformat()
        if session.disconnected_at
        else None,
    }


def dict_to_session(data: dict[str, Any]) -> WebSocketSession:
    return WebSocketSession(
        id=UUID(data["id"]),
        user_id=UUID(data["user_id"]),
        room_id=UUID(data["room_id"]),
        connected_at=datetime.fromisoformat(data["connected_at"]),
        last_ping_at=datetime.fromisoformat(data["last_ping_at"]),
        disconnected_at=datetime.fromisoformat(data["disconnected_at"])
        if data.get("disconnected_at")
        else None,
    )

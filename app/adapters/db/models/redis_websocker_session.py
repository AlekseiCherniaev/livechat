from typing import Any
from uuid import UUID
from datetime import datetime
from app.domain.entities.websocket_session import WebSocketSession


def session_to_dict(session: WebSocketSession) -> dict[str, Any]:
    return {
        "id": str(session.id),
        "user_id": str(session.user_id),
        "room_id": str(session.room_id),
        "session_id": str(session.session_id),
        "ip_address": session.ip_address,
        "connected_at": session.connected_at.isoformat(),
        "last_ping_at": session.last_ping_at.isoformat(),
    }


def dict_to_session(data: dict[str, Any]) -> WebSocketSession:
    return WebSocketSession(
        id=UUID(data["id"]),
        user_id=UUID(data["user_id"]),
        room_id=UUID(data["room_id"]),
        session_id=UUID(data["session_id"]),
        ip_address=data["ip_address"],
        connected_at=datetime.fromisoformat(data["connected_at"]),
        last_ping_at=datetime.fromisoformat(data["last_ping_at"]),
    )

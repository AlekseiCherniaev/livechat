from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.entities.user_session import UserSession


def session_to_dict(session: UserSession) -> dict[str, Any]:
    return {
        "id": str(session.id),
        "user_id": str(session.user_id),
        "connected_at": session.connected_at.isoformat(),
        "disconnected_at": session.disconnected_at.isoformat()
        if session.disconnected_at
        else None,
    }


def dict_to_session(dict_session: dict[str, Any]) -> UserSession:
    return UserSession(
        id=UUID(dict_session["id"]),
        user_id=UUID(dict_session["user_id"]),
        connected_at=datetime.fromisoformat(dict_session["connected_at"]),
        disconnected_at=(
            datetime.fromisoformat(dict_session["disconnected_at"])
            if dict_session["disconnected_at"]
            else None
        ),
    )

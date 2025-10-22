from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.domain.entities.user import User


def user_to_document(user: User) -> dict[str, Any]:
    return {
        "_id": str(user.id),
        "username": user.username,
        "hashed_password": user.hashed_password,
        "last_active": user.last_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def document_to_user(doc: dict[str, Any]) -> User:
    return User(
        id=UUID(doc["_id"]),
        username=doc["username"],
        hashed_password=doc["hashed_password"],
        last_active=doc.get("last_active"),
        created_at=doc.get("created_at", datetime.now(UTC)),
        updated_at=doc.get("updated_at", datetime.now(UTC)),
    )

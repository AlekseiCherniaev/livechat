from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.join_request import JoinRequest


@dataclass
class JoinRequestCreateDTO:
    message: str | None
    user_id: UUID
    room_id: UUID


@dataclass
class JoinRequestPublicDTO:
    id: UUID
    message: str | None
    username: str
    room_name: str


def join_request_to_dto(
    join_request: JoinRequest, room_name: str, username: str
) -> JoinRequestPublicDTO:
    return JoinRequestPublicDTO(
        id=join_request.id,
        message=join_request.message,
        username=username,
        room_name=room_name,
    )

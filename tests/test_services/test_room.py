from uuid import uuid4

import pytest
from pytest_asyncio import fixture

from app.domain.dtos.join_request import JoinRequestCreateDTO
from app.domain.dtos.room import RoomCreateDTO, RoomUpdateDTO
from app.domain.entities.join_request import JoinRequest
from app.domain.entities.room import Room
from app.domain.exceptions.join_request import (
    JoinRequestAlreadyExists,
)
from app.domain.exceptions.room import (
    RoomAlreadyExists,
    RoomNotFound,
    NoChangesDetected,
)
from app.domain.exceptions.user import UserNotFound
from app.domain.services.room import RoomService


class TestRoomService:
    @fixture
    def service(
        self,
        room_repo,
        user_repo,
        join_repo,
        membership_repo,
        outbox_repo,
        connection_port,
        tm,
    ):
        return RoomService(
            room_repo,
            user_repo,
            join_repo,
            membership_repo,
            outbox_repo,
            connection_port,
            tm,
        )

    async def test_create_room_success(
        self, service, room_repo, user_repo, outbox_repo, tm
    ):
        creator_id = uuid4()
        dto = RoomCreateDTO(
            name="My room",
            description="Desc",
            is_public=True,
            created_by=creator_id,
        )
        user_repo.get_by_id.return_value = object()
        room_repo.exists.return_value = False

        room = Room(
            name="My room", description="Desc", is_public=True, created_by=creator_id
        )
        room_repo.save.return_value = room

        await service.create_room(dto)

        room_repo.exists.assert_awaited_once_with(name="My room")
        user_repo.get_by_id.assert_awaited_once_with(user_id=creator_id)
        tm.run_in_transaction.assert_awaited_once()
        room_repo.save.assert_awaited()
        outbox_repo.save.assert_awaited()

    async def test_create_room_already_exists(self, service, room_repo):
        room_repo.exists.return_value = True
        dto = RoomCreateDTO(
            name="A", description="B", is_public=False, created_by=uuid4()
        )
        with pytest.raises(RoomAlreadyExists):
            await service.create_room(dto)

    async def test_create_room_user_not_found(self, service, room_repo, user_repo):
        room_repo.exists.return_value = False
        user_repo.get_by_id.return_value = None
        dto = RoomCreateDTO(
            name="A", description="B", is_public=False, created_by=uuid4()
        )
        with pytest.raises(UserNotFound):
            await service.create_room(dto)

    async def test_update_room_success(self, service, room_repo, outbox_repo, tm):
        created_by = uuid4()
        room = Room(
            id=uuid4(),
            name="Old",
            description="old",
            is_public=True,
            created_by=created_by,
        )
        room_repo.get_by_id.return_value = room
        room_repo.save.return_value = room

        dto = RoomUpdateDTO(
            description="new desc", is_public=None, created_by=created_by
        )

        result = await service.update_room(room.id, dto)
        assert result.description == "new desc"

        room_repo.save.assert_awaited_once()
        outbox_repo.save.assert_awaited_once()
        tm.run_in_transaction.assert_awaited_once()

    async def test_update_room_not_found(self, service, room_repo):
        room_repo.get_by_id.return_value = None
        with pytest.raises(RoomNotFound):
            await service.update_room(
                uuid4(), RoomUpdateDTO(description="x", created_by=uuid4())
            )

    async def test_update_room_no_changes(self, service, room_repo):
        created_by = uuid4()
        room = Room(
            id=uuid4(),
            name="A",
            description="same",
            is_public=True,
            created_by=created_by,
        )
        room_repo.get_by_id.return_value = room
        dto = RoomUpdateDTO(description="same", is_public=True, created_by=created_by)
        with pytest.raises(NoChangesDetected):
            await service.update_room(room.id, dto)

    async def test_delete_room_success(self, service, room_repo, outbox_repo, tm):
        created_by = uuid4()
        room = Room(
            id=uuid4(), name="R", description="", is_public=True, created_by=created_by
        )
        room_repo.get_by_id.return_value = room

        await service.delete_room(room_id=room.id, created_by=created_by)

        room_repo.delete_by_id.assert_awaited_once()
        outbox_repo.save.assert_awaited_once()
        tm.run_in_transaction.assert_awaited_once()

    async def test_delete_room_not_found(self, service, room_repo):
        room_repo.get_by_id.return_value = None
        with pytest.raises(RoomNotFound):
            await service.delete_room(uuid4(), created_by=uuid4())

    async def test_get_room_success(self, service, room_repo):
        room = Room(
            id=uuid4(), name="N", description="", is_public=True, created_by=uuid4()
        )
        room_repo.get_by_id.return_value = room
        result = await service.get_room(room.id)
        assert result.name == "N"

    async def test_get_room_not_found(self, service, room_repo):
        room_repo.get_by_id.return_value = None
        with pytest.raises(RoomNotFound):
            await service.get_room(uuid4())

    async def test_list_rooms_for_user(self, service, membership_repo):
        rooms = [
            Room(
                id=uuid4(), name="A", description="", is_public=True, created_by=uuid4()
            ),
            Room(
                id=uuid4(), name="B", description="", is_public=True, created_by=uuid4()
            ),
        ]
        membership_repo.list_rooms_for_user.return_value = rooms
        result = await service.list_rooms_for_user(uuid4())
        assert len(result) == 2

    async def test_request_join_public_room(
        self, service, room_repo, user_repo, tm, outbox_repo, membership_repo
    ):
        rid, uid = uuid4(), uuid4()
        room = Room(id=rid, name="Pub", is_public=True, created_by=uuid4())
        user = type("User", (), {"id": uid, "username": "john"})
        room_repo.get_by_id.return_value = room
        user_repo.get_by_id.return_value = user

    async def test_request_join_private_room_duplicate(
        self, service, room_repo, user_repo, join_repo, membership_repo
    ):
        rid, uid = uuid4(), uuid4()
        room = Room(id=rid, name="Priv", is_public=False, created_by=uuid4())
        user = type("User", (), {"id": uid, "username": "john"})
        room_repo.get_by_id.return_value = room
        user_repo.get_by_id.return_value = user
        join_repo.exists.return_value = True
        membership_repo.exists.return_value = False

        dto = type("DTO", (), {"room_id": rid, "user_id": uid, "message": None})
        with pytest.raises(JoinRequestAlreadyExists):
            await service.request_join(dto)

    async def test_request_join_room_not_found(self, service, room_repo):
        room_repo.get_by_id.return_value = None
        with pytest.raises(RoomNotFound):
            await service.request_join(
                JoinRequestCreateDTO(room_id=uuid4(), user_id=uuid4(), message=None)
            )

    async def test_request_join_user_not_found(self, service, room_repo, user_repo):
        room_repo.get_by_id.return_value = Room(
            id=uuid4(), name="x", is_public=False, created_by=uuid4()
        )
        user_repo.get_by_id.return_value = None
        with pytest.raises(UserNotFound):
            await service.request_join(
                JoinRequestCreateDTO(room_id=uuid4(), user_id=uuid4(), message=None)
            )

    async def test_handle_join_request_accept(
        self, service, join_repo, room_repo, tm, outbox_repo
    ):
        rid, uid = uuid4(), uuid4()
        req = JoinRequest(id=uuid4(), room_id=rid, user_id=uid)
        created_by = uuid4()
        join_repo.get_by_id.return_value = req
        room_repo.get_by_id.return_value = Room(
            id=rid, name="R", created_by=created_by, is_public=True
        )

        await service.handle_join_request(req.id, accept=True, created_by=created_by)

        join_repo.delete_by_id.assert_awaited_once()
        outbox_repo.save.assert_awaited()
        tm.run_in_transaction.assert_awaited_once()

    async def test_handle_join_request_not_found(self, service, join_repo):
        join_repo.get_by_id.return_value = None
        with pytest.raises(Exception):
            await service.handle_join_request(uuid4(), uuid4(), accept=True)

    async def test_handle_join_request_room_not_found(
        self, service, join_repo, room_repo
    ):
        req = JoinRequest(
            id=uuid4(),
            room_id=uuid4(),
            user_id=uuid4(),
        )
        join_repo.get_by_id.return_value = req
        room_repo.get_by_id.return_value = None
        with pytest.raises(RoomNotFound):
            await service.handle_join_request(req.id, accept=True, created_by=uuid4())

    async def test_remove_participant_non_creator(
        self, service, room_repo, membership_repo, tm, outbox_repo
    ):
        creator_id = uuid4()
        rid, uid = uuid4(), uuid4()
        room = Room(id=rid, name="A", created_by=creator_id, is_public=True)
        room_repo.get_by_id.return_value = room

        await service.remove_participant(rid, uid, created_by=creator_id)

        membership_repo.delete.assert_awaited_once()
        room_repo.remove_participant.assert_awaited_once()
        outbox_repo.save.assert_awaited_once()
        tm.run_in_transaction.assert_awaited_once()

    async def test_remove_participant_room_not_found(self, service, room_repo):
        room_repo.get_by_id.return_value = None
        with pytest.raises(RoomNotFound):
            await service.remove_participant(uuid4(), uuid4(), created_by=uuid4())

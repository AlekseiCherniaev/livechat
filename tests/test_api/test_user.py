import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUsersAPI:
    async def test_register_success(self, async_client: AsyncClient):
        payload = {"username": "alice", "password": "secret"}
        response = await async_client.post("/api/users/register", json=payload)
        assert response.status_code == 200

    async def test_register_user_already_exists(self, async_client: AsyncClient):
        payload = {"username": "bob", "password": "secret"}
        await async_client.post("/api/users/register", json=payload)
        response = await async_client.post("/api/users/register", json=payload)
        assert response.status_code == 400

    async def test_login_success(self, async_client: AsyncClient):
        payload = {"username": "charlie", "password": "secret"}
        await async_client.post("/api/users/register", json=payload)

        response = await async_client.post("/api/users/login", json=payload)
        assert response.status_code == 200
        assert "session_id" in response.cookies

    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        payload = {"username": "dave", "password": "secret"}
        await async_client.post("/api/users/register", json=payload)

        wrong_payload = {"username": "dave", "password": "wrong"}
        response = await async_client.post("/api/users/login", json=wrong_payload)
        assert response.status_code == 401

    async def test_me_success(self, async_client: AsyncClient):
        payload = {"username": "eve", "password": "secret"}
        await async_client.post("/api/users/register", json=payload)
        login_resp = await async_client.post("/api/users/login", json=payload)

        cookies = {"session_id": login_resp.cookies["session_id"]}
        resp = await async_client.get("/api/users/me", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "eve"

    async def test_me_invalid_session(self, async_client: AsyncClient):
        resp = await async_client.get(
            "/api/users/me", cookies={"session_id": "invalid"}
        )
        assert resp.status_code == 401

    async def test_logout_success(self, async_client: AsyncClient):
        payload = {"username": "frank", "password": "secret"}
        await async_client.post("/api/users/register", json=payload)
        login_resp = await async_client.post("/api/users/login", json=payload)

        cookies = {"session_id": login_resp.cookies["session_id"]}
        resp = await async_client.post("/api/users/logout", cookies=cookies)
        assert resp.status_code == 200
        assert "session_id" not in resp.cookies

    async def test_logout_no_session(self, async_client: AsyncClient):
        resp = await async_client.post("/api/users/logout")
        assert resp.status_code == 404

    async def test_full_flow(self, async_client: AsyncClient):
        payload = {"username": "grace", "password": "secret"}

        # register
        reg_resp = await async_client.post("/api/users/register", json=payload)
        assert reg_resp.status_code == 200

        # login
        login_resp = await async_client.post("/api/users/login", json=payload)
        assert login_resp.status_code == 200
        session_id = login_resp.cookies["session_id"]

        # me
        me_resp = await async_client.get(
            "/api/users/me", cookies={"session_id": session_id}
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["username"] == "grace"

        # logout
        logout_resp = await async_client.post(
            "/api/users/logout", cookies={"session_id": session_id}
        )
        assert logout_resp.status_code == 200

        # me after logout should fail
        me_after_logout = await async_client.get(
            "/api/users/me", cookies={"session_id": session_id}
        )
        assert me_after_logout.status_code == 404

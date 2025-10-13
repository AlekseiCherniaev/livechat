class TestAPI:
    async def test_docs_endpoint(self, async_client):
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

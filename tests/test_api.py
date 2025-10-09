from pytest_asyncio import fixture
from starlette.testclient import TestClient

from app.app import init_app


@fixture
def test_client():
    return TestClient(app=init_app())


class TestAPI:
    def test_docs_endpoint(self, test_client):
        response = test_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

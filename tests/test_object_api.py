import pytest
from httpx import AsyncClient, post as httpx_post
from httpx import ASGITransport
from unittest.mock import AsyncMock, MagicMock
from fastapi import status


from app.main import app
from app.api import objects
from app.models.objects import ObjectCreateRequest


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer secret-token"}


@pytest.mark.asyncio
async def test_post_object_mocked(monkeypatch, auth_headers):
    monkeypatch.setattr(objects, "verify_token", AsyncMock(return_value={"user_id": 1, "role": "admin"}))

    # Mock DB result
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (777, "1")

    mock_conn = AsyncMock()
    mock_conn.__aenter__.return_value.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn

    monkeypatch.setattr(objects, "engine", mock_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "id": 110,
            "up": 1,
            "attrs": {"t110": "Mocked Name"}
        }
        response = await client.post("/object", headers=auth_headers, json=payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 777
    assert response.json()["val"] == "Mocked Name"


@pytest.mark.parametrize("payload", [
    {
        "id": 101,
        "up": 1,
        "attrs": {
            "t101": "Ellipse",
        }
    },
])
def test_post_object_real_server(payload):
    response = httpx_post(
        "http://localhost:8000/object",
        headers={"Authorization": "Bearer secret-token"},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["val"] == payload["attrs"][f"t{payload['id']}"]
    assert data["t"] == payload["id"]
    assert data["up"] == payload["up"]

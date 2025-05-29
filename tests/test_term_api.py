import pytest
from fastapi import status
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from httpx import post as httpx_post

from app.main import app
from app.api import terms


@pytest.fixture
def auth_headers():
    """Returns mock Authorization header for tests."""
    return {"Authorization": "Bearer secret-token"}


# Sample mocked response representing a term with empty requisites.
MOCKED_TERM = {
    "id": 64,
    "up": 0,
    "base": 3,
    "obj": "Пользователь",
    "uniq": 1,
    "req_id": None,
    "req_t": None,
    "req_val": None,
    "ref_val": None,
    "default_val": None,
    "mods": None,
    "attrs": None,
    "ref_id": None,
    "ord": None,
}


def setup_engine_mock(return_value):
    """Creates a mocked SQLAlchemy engine with predefined query result.

    Args:
        return_value: The list of dictionaries to return as query result.

    Returns:
        A MagicMock instance simulating the async SQLAlchemy engine.
    """
    mock_engine = MagicMock()
    mock_conn = AsyncMock()
    mock_result = MagicMock()

    # Simulate the chain: result.mappings().all() → return predefined rows.
    mock_result.mappings.return_value.all.return_value = return_value
    mock_conn.__aenter__.return_value.execute.return_value = mock_result
    mock_engine.connect.return_value = mock_conn
    return mock_engine


@pytest.mark.asyncio
async def test_get_all_terms(monkeypatch, auth_headers):
    """Tests the GET /term endpoint with mocked DB and auth."""
    monkeypatch.setattr(terms, "verify_token", AsyncMock(
        return_value={"user_id": 1, "role": "admin"}))
    monkeypatch.setattr(terms, "engine", setup_engine_mock([MOCKED_TERM]))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert response.json()[0]["id"] == MOCKED_TERM["id"]


@pytest.mark.asyncio
async def test_get_term_by_id(monkeypatch, auth_headers):
    """Tests the GET /term/{term_id} endpoint with valid mocked result."""
    monkeypatch.setattr(terms, "verify_token", AsyncMock(
        return_value={"user_id": 1, "role": "admin"}))
    monkeypatch.setattr(terms, "engine", setup_engine_mock([MOCKED_TERM]))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term/64", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == MOCKED_TERM["id"]


@pytest.mark.asyncio
async def test_get_term_by_id_not_found(monkeypatch, auth_headers):
    """Tests the GET /term/{term_id} endpoint with no matching term in DB."""
    monkeypatch.setattr(terms, "verify_token", AsyncMock(
        return_value={"user_id": 1, "role": "admin"}))
    monkeypatch.setattr(terms, "engine", setup_engine_mock([]))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/term/999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Term 999 not found"
    
@pytest.mark.parametrize("payload", [
    {"val": "operat1'1ion143336", "t": 3, "mods": {}},
    {"val": "operatn143336", "t": 3, "mods": {}},
    {"val": "operation112", "t": 3, "mods": {}},
    {"val": "ope'ration3467", "t": 3, "mods": {"UNIQUE": "", "ALIAS": "tnx"}},
])
def test_create_term_real_server(payload):
    """Integration test for POST /term (requires live server)"""
    response = httpx_post(
        "http://localhost:8000/term",
        headers={"Authorization": "Bearer secret-token"},
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["val"] == payload["val"]
    assert data["t"] == payload["t"]
    
    
@pytest.mark.asyncio
async def test_post_term_mocked(monkeypatch, auth_headers):
    monkeypatch.setattr(terms, "verify_token", AsyncMock(return_value={"user_id": 1, "role": "admin"}))
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (123, "1")

    mock_conn_ctx = AsyncMock()
    mock_conn_ctx.__aenter__.return_value.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.begin.return_value = mock_conn_ctx

    monkeypatch.setattr(terms, "engine", mock_engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"val": "Оператор", "t": 3, "mods": {"UNIQUE": "", "ALIAS": "Operator"}}
        response = await client.post("/term", headers=auth_headers, json=payload)

    assert response.status_code == 200
    assert response.json()["id"] == 123
    assert response.json()["t"] == 3
    assert response.json()["val"] == "Оператор"

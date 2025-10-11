"""Tests for rate limiting and DDoS protection."""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_rate_limit_on_create_object():
    """Test that rate limiting is applied to object creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First 10 requests should succeed (rate limit is 10/minute)
        for i in range(10):
            response = await client.post(
                "/testdb/objects",
                json={"id": 1, "up": 1, "attrs": {}},
                headers={"Authorization": "secret-token"},
            )
            # We expect either success or other errors (not 429)
            assert response.status_code != 429, f"Request {i+1} was rate limited"

        # 11th request should be rate limited
        response = await client.post(
            "/testdb/objects",
            json={"id": 1, "up": 1, "attrs": {}},
            headers={"Authorization": "secret-token"},
        )
        assert response.status_code == 429, "Expected rate limit exceeded error"


@pytest.mark.asyncio
async def test_request_size_limit():
    """Test that request size limit middleware rejects large payloads."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a payload larger than 1MB
        large_payload = {
            "id": 1,
            "up": 1,
            "attrs": {"data": "x" * (1_000_001)},  # Slightly over 1MB
        }

        response = await client.post(
            "/testdb/objects",
            json=large_payload,
            headers={
                "Authorization": "secret-token",
                "Content-Length": str(len(str(large_payload))),
            },
        )

        # Should be rejected due to size limit (413 Payload Too Large)
        assert response.status_code == 413, "Expected payload too large error"


@pytest.mark.asyncio
async def test_rate_limit_on_get_requests():
    """Test that rate limiting is applied to GET endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First 30 requests should succeed (rate limit is 30/minute for GET)
        for i in range(30):
            response = await client.get(
                "/testdb/terms",
                headers={"Authorization": "secret-token"},
            )
            # We expect either success or other errors (not 429)
            assert response.status_code != 429, f"Request {i+1} was rate limited"

        # 31st request should be rate limited
        response = await client.get(
            "/testdb/terms",
            headers={"Authorization": "secret-token"},
        )
        assert response.status_code == 429, "Expected rate limit exceeded error"


@pytest.mark.asyncio
async def test_rate_limit_different_endpoints():
    """Test that rate limits are independent per endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Hit rate limit on create_object (10/minute)
        for i in range(11):
            response = await client.post(
                "/testdb/objects",
                json={"id": 1, "up": 1, "attrs": {}},
                headers={"Authorization": "secret-token"},
            )

        # Last request should be rate limited
        assert response.status_code == 429

        # But we should still be able to access other endpoints
        response = await client.get(
            "/testdb/terms",
            headers={"Authorization": "secret-token"},
        )
        # Should not be rate limited on different endpoint
        assert response.status_code != 429, "Different endpoint should not be affected"

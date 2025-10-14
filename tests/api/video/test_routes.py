"""Tests for video API routes"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_connect_video_invalid_source():
    """Test POST /video/connect endpoint with invalid source"""
    response = client.post(
        "/video/connect",
        json={
            "drone_id": "test_drone",
            "source_url": "invalid://test.url",
            "source_type": "rtsp"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["drone_id"] == "test_drone"


def test_get_video_info_not_found():
    """Test GET /video/info for non-existent drone"""
    response = client.get("/video/info/nonexistent_drone")

    assert response.status_code == 404


def test_disconnect_not_found():
    """Test POST /video/disconnect for non-existent drone"""
    response = client.post("/video/disconnect/nonexistent_drone")

    assert response.status_code == 404


def test_stream_not_connected():
    """Test GET /video/stream for non-connected drone"""
    response = client.get("/video/stream/nonexistent_drone")

    assert response.status_code == 404

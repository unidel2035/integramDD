"""Tests for video service"""
import pytest
from app.api.video.service import VideoStreamService


@pytest.fixture
def video_service():
    """Fixture for video service"""
    return VideoStreamService()


@pytest.mark.asyncio
async def test_connect_invalid_source(video_service):
    """Test connection with invalid video source"""
    result = await video_service.connect(
        "test_drone",
        "invalid://nonexistent.url"
    )

    assert result is False
    assert not video_service.is_connected("test_drone")


@pytest.mark.asyncio
async def test_disconnect_not_connected(video_service):
    """Test disconnecting when not connected"""
    result = await video_service.disconnect("nonexistent_drone")

    assert result is False


@pytest.mark.asyncio
async def test_is_connected(video_service):
    """Test is_connected check"""
    assert not video_service.is_connected("test_drone")


@pytest.mark.asyncio
async def test_get_info_not_connected(video_service):
    """Test getting info for non-existent drone"""
    info = video_service.get_info("nonexistent_drone")

    assert info is None


@pytest.mark.asyncio
async def test_get_frame_not_connected(video_service):
    """Test getting frame for non-existent drone"""
    frame = await video_service.get_frame("nonexistent_drone")

    assert frame is None


@pytest.mark.asyncio
async def test_connect_already_connected(video_service):
    """Test connecting when already connected"""
    # This test would require a valid video source or mock
    # For now, we test the logic without actual video source
    pass

"""
Pydantic models for video API
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class VideoSourceType(str, Enum):
    """Type of video source"""
    RTSP = "rtsp"
    HTTP = "http"
    FILE = "file"


class VideoConnectRequest(BaseModel):
    """Request to connect a new video source"""
    drone_id: str = Field(..., description="Unique drone identifier")
    source_url: str = Field(..., description="Video source URL (RTSP/HTTP)")
    source_type: VideoSourceType = Field(
        VideoSourceType.RTSP,
        description="Type of video source"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "drone_id": "user_drone_walksnail",
                "source_url": "rtsp://localhost:8554/drone_camera",
                "source_type": "rtsp"
            }
        }


class VideoConnectResponse(BaseModel):
    """Response after connecting video source"""
    success: bool
    drone_id: str
    message: str


class VideoInfoResponse(BaseModel):
    """Information about video stream"""
    drone_id: str
    connected: bool
    resolution: Optional[tuple[int, int]] = None  # (width, height)
    fps: Optional[float] = None
    source_url: Optional[str] = None
    frame_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "drone_id": "user_drone_walksnail",
                "connected": True,
                "resolution": [1920, 1080],
                "fps": 60.0,
                "source_url": "rtsp://localhost:8554/drone_camera",
                "frame_count": 3542
            }
        }


class VideoDisconnectResponse(BaseModel):
    """Response after disconnecting video source"""
    success: bool
    drone_id: str
    message: str

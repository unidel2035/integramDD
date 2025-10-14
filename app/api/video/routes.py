"""
FastAPI routes for video streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
import cv2
import logging
from typing import AsyncGenerator

from .models import (
    VideoConnectRequest,
    VideoConnectResponse,
    VideoInfoResponse,
    VideoDisconnectResponse
)
from .service import video_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["video"])


@router.post("/connect", response_model=VideoConnectResponse)
async def connect_video(request: VideoConnectRequest):
    """
    Connect to a video source for a drone

    Args:
        request: VideoConnectRequest with drone_id and source_url

    Returns:
        VideoConnectResponse with connection status
    """
    success = await video_service.connect(
        request.drone_id,
        request.source_url
    )

    if success:
        return VideoConnectResponse(
            success=True,
            drone_id=request.drone_id,
            message=f"Successfully connected to video source"
        )
    else:
        return VideoConnectResponse(
            success=False,
            drone_id=request.drone_id,
            message=f"Failed to connect to video source"
        )


@router.post("/disconnect/{drone_id}", response_model=VideoDisconnectResponse)
async def disconnect_video(drone_id: str):
    """
    Disconnect from a video source

    Args:
        drone_id: Unique identifier for the drone

    Returns:
        VideoDisconnectResponse with disconnection status
    """
    success = await video_service.disconnect(drone_id)

    if success:
        return VideoDisconnectResponse(
            success=True,
            drone_id=drone_id,
            message=f"Successfully disconnected video source"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Drone {drone_id} not connected"
        )


@router.get("/info/{drone_id}", response_model=VideoInfoResponse)
async def get_video_info(drone_id: str):
    """
    Get information about a video stream

    Args:
        drone_id: Unique identifier for the drone

    Returns:
        VideoInfoResponse with stream information
    """
    if not video_service.is_connected(drone_id):
        raise HTTPException(
            status_code=404,
            detail=f"Drone {drone_id} not connected"
        )

    info = video_service.get_info(drone_id)

    return VideoInfoResponse(
        drone_id=drone_id,
        connected=True,
        resolution=info["resolution"],
        fps=info["fps"],
        source_url=info["source_url"],
        frame_count=info["frame_count"]
    )


@router.get("/stream/{drone_id}")
async def video_stream_http(drone_id: str):
    """
    HTTP MJPEG video stream

    Args:
        drone_id: Unique identifier for the drone

    Returns:
        StreamingResponse with MJPEG stream
    """
    if not video_service.is_connected(drone_id):
        raise HTTPException(
            status_code=404,
            detail=f"Drone {drone_id} not connected"
        )

    async def generate() -> AsyncGenerator[bytes, None]:
        """Generate MJPEG frames"""
        try:
            while True:
                frame = await video_service.get_frame(drone_id)

                if frame is None:
                    break

                # Encode frame as JPEG
                _, buffer = cv2.imencode(
                    '.jpg',
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 80]
                )

                # Yield as multipart frame
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' +
                    buffer.tobytes() +
                    b'\r\n'
                )

        except Exception as e:
            logger.error(f"Error in video stream: {e}")

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.websocket("/stream/ws/{drone_id}")
async def video_stream_websocket(websocket: WebSocket, drone_id: str):
    """
    WebSocket video stream

    Args:
        websocket: WebSocket connection
        drone_id: Unique identifier for the drone
    """
    if not video_service.is_connected(drone_id):
        await websocket.close(code=1008, reason="Drone not connected")
        return

    await websocket.accept()
    logger.info(f"WebSocket video stream connected for {drone_id}")

    try:
        while True:
            frame = await video_service.get_frame(drone_id)

            if frame is None:
                break

            # Encode frame as JPEG
            _, buffer = cv2.imencode(
                '.jpg',
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 80]
            )

            # Send frame as binary data
            await websocket.send_bytes(buffer.tobytes())

    except WebSocketDisconnect:
        logger.info(f"WebSocket video stream disconnected for {drone_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket video stream: {e}")
    finally:
        await websocket.close()

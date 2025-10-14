"""
Video capture service for drone video streaming
"""
import cv2
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class VideoStreamService:
    """Service for managing drone video streams"""

    def __init__(self):
        self._captures: Dict[str, cv2.VideoCapture] = {}
        self._frame_queues: Dict[str, asyncio.Queue] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._info: Dict[str, dict] = {}

    async def connect(
        self,
        drone_id: str,
        source_url: str
    ) -> bool:
        """
        Connect to a video source and start capturing

        Args:
            drone_id: Unique identifier for the drone
            source_url: URL of video source (RTSP, HTTP, or file path)

        Returns:
            bool: True if connected successfully
        """
        if drone_id in self._captures:
            logger.warning(f"Drone {drone_id} already connected")
            return False

        try:
            # Open video capture
            cap = cv2.VideoCapture(source_url)

            if not cap.isOpened():
                logger.error(f"Failed to open video source: {source_url}")
                return False

            # Get video info
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            self._captures[drone_id] = cap
            self._frame_queues[drone_id] = asyncio.Queue(maxsize=2)
            self._info[drone_id] = {
                "resolution": (width, height),
                "fps": fps,
                "source_url": source_url,
                "frame_count": 0,
                "connected_at": datetime.now()
            }

            # Start capture task
            task = asyncio.create_task(self._capture_loop(drone_id))
            self._tasks[drone_id] = task

            logger.info(
                f"Connected to video source for {drone_id}: "
                f"{width}x{height} @ {fps} fps"
            )
            return True

        except Exception as e:
            logger.error(f"Error connecting to video source: {e}")
            return False

    async def disconnect(self, drone_id: str) -> bool:
        """
        Disconnect from a video source

        Args:
            drone_id: Unique identifier for the drone

        Returns:
            bool: True if disconnected successfully
        """
        if drone_id not in self._captures:
            logger.warning(f"Drone {drone_id} not connected")
            return False

        try:
            # Cancel capture task
            if drone_id in self._tasks:
                self._tasks[drone_id].cancel()
                try:
                    await self._tasks[drone_id]
                except asyncio.CancelledError:
                    pass
                del self._tasks[drone_id]

            # Release capture
            self._captures[drone_id].release()
            del self._captures[drone_id]

            # Clear queue
            if drone_id in self._frame_queues:
                del self._frame_queues[drone_id]

            # Clear info
            if drone_id in self._info:
                del self._info[drone_id]

            logger.info(f"Disconnected video source for {drone_id}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting video source: {e}")
            return False

    async def _capture_loop(self, drone_id: str):
        """
        Background task to capture frames from video source

        Args:
            drone_id: Unique identifier for the drone
        """
        cap = self._captures[drone_id]
        queue = self._frame_queues[drone_id]

        logger.info(f"Started capture loop for {drone_id}")

        try:
            while True:
                ret, frame = cap.read()

                if not ret:
                    logger.warning(
                        f"Failed to read frame from {drone_id}, "
                        f"attempting reconnect..."
                    )
                    # Try to reconnect
                    await asyncio.sleep(1)
                    source_url = self._info[drone_id]["source_url"]
                    cap.release()
                    cap = cv2.VideoCapture(source_url)
                    self._captures[drone_id] = cap

                    if not cap.isOpened():
                        logger.error(f"Failed to reconnect {drone_id}")
                        break
                    continue

                # Update frame count
                self._info[drone_id]["frame_count"] += 1

                # Put frame in queue (non-blocking, drop old frames)
                if queue.full():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass

                await queue.put(frame)

                # Small delay to avoid CPU overload
                await asyncio.sleep(0.001)

        except asyncio.CancelledError:
            logger.info(f"Capture loop cancelled for {drone_id}")
        except Exception as e:
            logger.error(f"Error in capture loop for {drone_id}: {e}")
        finally:
            cap.release()

    async def get_frame(self, drone_id: str) -> Optional[np.ndarray]:
        """
        Get the latest frame for a drone

        Args:
            drone_id: Unique identifier for the drone

        Returns:
            numpy.ndarray: Frame image or None if not available
        """
        if drone_id not in self._frame_queues:
            return None

        queue = self._frame_queues[drone_id]

        try:
            # Wait for frame with timeout
            frame = await asyncio.wait_for(queue.get(), timeout=1.0)
            return frame
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for frame from {drone_id}")
            return None

    def get_info(self, drone_id: str) -> Optional[dict]:
        """
        Get information about a video stream

        Args:
            drone_id: Unique identifier for the drone

        Returns:
            dict: Stream information or None if not connected
        """
        return self._info.get(drone_id)

    def is_connected(self, drone_id: str) -> bool:
        """
        Check if a drone is connected

        Args:
            drone_id: Unique identifier for the drone

        Returns:
            bool: True if connected
        """
        return drone_id in self._captures


# Global service instance
video_service = VideoStreamService()

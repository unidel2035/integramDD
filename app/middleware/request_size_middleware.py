"""Request size limiting middleware to prevent oversized payloads."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.settings import settings


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit the maximum size of incoming requests."""

    def __init__(self, app, max_request_size: int = None):
        super().__init__(app)
        self.max_request_size = max_request_size or settings.MAX_REQUEST_SIZE

    async def dispatch(self, request: Request, call_next):
        """Check request size before processing."""
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=413,
                detail=f"Request body too large. Maximum allowed size is {self.max_request_size} bytes.",
            )

        return await call_next(request)

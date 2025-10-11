"""Middleware to limit the size of incoming HTTP requests."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce a maximum request body size limit."""

    def __init__(self, app, max_request_size: int = 1_000_000):
        """
        Initialize the middleware.

        Args:
            app: The FastAPI application instance.
            max_request_size: Maximum allowed request body size in bytes (default: 1MB).
        """
        super().__init__(app)
        self.max_request_size = max_request_size

    async def dispatch(self, request: Request, call_next):
        """
        Check the content-length header and reject requests that are too large.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            Response from the next handler or an HTTP 413 error.
        """
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=413,
                detail=f"Request body too large. Maximum allowed size is {self.max_request_size} bytes.",
            )

        return await call_next(request)

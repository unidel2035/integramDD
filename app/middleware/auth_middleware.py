
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.auth.auth import verify_token

EXCLUDE_PATHS = {"/docs", "/openapi.json", "/health"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDE_PATHS:
            return await call_next(request)

        try:
            token = request.headers.get("Authorization")
            if not token:
                raise HTTPException(status_code=401, detail="Missing token")
            verify_token(token)  # или просто verify_token(...) если sync
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

        return await call_next(request)

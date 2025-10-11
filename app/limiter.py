"""Rate limiter instance for the application."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.settings import settings

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, enabled=settings.RATE_LIMIT_ENABLED)

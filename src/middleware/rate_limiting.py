"""
Rate limiting configuration using slowapi library.
"""

from fastapi import HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import PlainTextResponse

from src.shared.config import config
from src.shared.utils import logger


# Initialize limiter with proper configuration
def create_limiter():
    """Create limiter with Redis backend (fallback to memory)."""
    rate_str = f"{config.rate_limit.requests_per_hour}/{config.rate_limit.window_seconds} second"
    limiter_kwargs = {"key_func": get_remote_address, "default_limits": [rate_str]}

    # Add Redis storage if configured
    if config.rate_limit.redis_url:
        limiter_kwargs["storage_uri"] = config.rate_limit.redis_url
        logger.info(
            f"Rate limiting initialized with Redis: {config.rate_limit.redis_url}"
        )
    else:
        logger.info("Rate limiting initialized with in-memory storage")

    return Limiter(**limiter_kwargs)


# Create limiter instance
limiter = create_limiter()


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler with proper headers."""
    retry_after = exc.detail.get("remaining", 0) if hasattr(exc, "detail") else 0
    headers = {"Retry-After": str(retry_after)} if retry_after else {}

    return PlainTextResponse("Too Many Requests", status_code=429, headers=headers)


# Rate limit decorators for different endpoint types
def auth_rate_limit():
    """Rate limit for authentication endpoints."""
    return limiter.limit("5/minute")


def api_rate_limit():
    """Rate limit for general API endpoints."""
    return limiter.limit(f"{config.rate_limit.requests_per_hour}/hour")


def processing_rate_limit():
    """Rate limit for image processing endpoints."""
    return limiter.limit("10/hour")


def status_rate_limit():
    """Rate limit for status check endpoints."""
    return limiter.limit("200/hour")


def admin_rate_limit():
    """Rate limit for admin endpoints."""
    return limiter.limit("50/hour")


def burst_rate_limit():
    """Rate limit for burst requests."""
    return limiter.limit(f"{config.rate_limit.burst_limit}/minute")

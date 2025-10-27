"""
Security middleware for headers and CORS.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response as StarletteResponse

from src.shared.config import config
from src.shared.utils import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add essential security headers and request size limiting."""

    def __init__(self, app):
        super().__init__(app)
        self.max_request_size = 10 * 1024 * 1024  # 10MB default

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        # Basic request size limit
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_request_size:
                    return StarletteResponse("Request too large", status_code=413)
            except ValueError:
                pass

        response = await call_next(request)

        # Essential security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"

        return response

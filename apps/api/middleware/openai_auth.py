"""Bearer authentication middleware for OpenAI compatibility.

Extracts Bearer tokens from Authorization header and maps to X-API-Key
for OpenAI-compatible endpoints at /v1/*.
"""

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to extract Bearer token and map to X-API-Key for /v1/* routes.

    This middleware enables OpenAI client compatibility by accepting
    Authorization: Bearer tokens and converting them to X-API-Key headers
    that our existing ApiKeyAuthMiddleware expects.

    Only affects routes starting with /v1/ (OpenAI-compatible endpoints).
    Existing /api/v1/* routes are not modified.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with Bearer token extraction for /v1/* routes.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response from next handler.
        """
        # Only process /v1/* routes (OpenAI-compatible endpoints)
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)

        # Don't overwrite existing X-API-Key header
        if "X-API-Key" in request.headers:
            return await call_next(request)

        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        auth_header_stripped = auth_header.strip()
        if auth_header_stripped.lower().startswith("bearer "):
            bearer_token = auth_header_stripped[7:].strip()  # Remove "Bearer " prefix
            if not bearer_token:
                return await call_next(request)

            # Add X-API-Key header to request scope
            # request.scope["headers"] is a list of (name, value) byte tuples
            # We need to convert properly using MutableHeaders
            headers = MutableHeaders(scope=request.scope)
            headers["X-API-Key"] = bearer_token

        return await call_next(request)

"""API key authentication middleware."""

import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.api.config import get_settings

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/api/v1/health",
    "/api/v1/mcp-servers/share",
    "/docs",
    "/redoc",
    "/openapi.json",
}

PUBLIC_PATH_PREFIXES = ("/api/v1/mcp-servers/share/",)


class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key for protected routes."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with API key validation.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response.
        """
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith(
            PUBLIC_PATH_PREFIXES
        ):
            return await call_next(request)

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "Missing API key",
                        "details": {},
                    }
                },
            )

        # Validate API key
        settings = get_settings()
        if not secrets.compare_digest(api_key, settings.api_key.get_secret_value()):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "AUTHENTICATION_ERROR",
                        "message": "Invalid API key",
                        "details": {},
                    }
                },
            )

        # Store validated API key in request state
        request.state.api_key = api_key

        return await call_next(request)

"""Rate limiting middleware using slowapi (T124)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response as StarletteResponse

from apps.api.config import get_settings


def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting.

    Only trusts X-Forwarded-For header when explicitly configured
    (trust_proxy_headers=True). When trusted, uses the rightmost IP
    which is harder to spoof than the leftmost.

    Args:
        request: FastAPI request object.

    Returns:
        Client IP address string.
    """
    settings = get_settings()

    # Only trust forwarded headers when explicitly configured
    if settings.trust_proxy_headers:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Use rightmost IP - added by trusted proxy, harder to spoof
            # The leftmost IP can be easily spoofed by clients
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            if ips:
                return ips[-1]

    # Fall back to direct client address
    return get_remote_address(request)


def get_api_key(request: Request) -> str:
    """Get API key for rate limiting by key instead of IP.

    This allows rate limiting per API key, which is more
    appropriate for authenticated APIs.

    Args:
        request: FastAPI request object.

    Returns:
        API key or fallback to IP address.
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    return get_client_ip(request)


# Create limiter with API key-based identification
limiter = Limiter(key_func=get_api_key)


async def rate_limit_handler(
    _request: Request, exc: Exception
) -> StarletteResponse:
    """Handle rate limit exceeded errors.

    Args:
        _request: The request that exceeded the limit (unused).
        exc: The rate limit exceeded exception.

    Returns:
        JSON response with rate limit error details.
    """
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {exc.detail}",
                    "details": {"retry_after": getattr(exc, "retry_after", None)},
                }
            },
            headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
        )
    # Fallback for unexpected exception types
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Unexpected error"}},
    )


def configure_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance.
    """
    # Store limiter in app state for route-level access
    app.state.limiter = limiter

    # Add rate limit exceeded handler with proper signature
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# Rate limit values for different endpoint types
def get_query_rate_limit() -> str:
    """Get rate limit for query endpoints - more restrictive.

    Returns:
        Rate limit string (e.g., "10/minute").
    """
    settings = get_settings()
    # Default: 10 queries per minute
    return f"{settings.rate_limit_query_per_minute}/minute"


def get_session_rate_limit() -> str:
    """Get rate limit for session endpoints - moderate.

    Returns:
        Rate limit string.
    """
    settings = get_settings()
    # Default: 30 session operations per minute
    return f"{settings.rate_limit_session_per_minute}/minute"


def get_general_rate_limit() -> str:
    """Get rate limit for general endpoints - permissive.

    Returns:
        Rate limit string.
    """
    settings = get_settings()
    # Default: 100 requests per minute
    return f"{settings.rate_limit_general_per_minute}/minute"

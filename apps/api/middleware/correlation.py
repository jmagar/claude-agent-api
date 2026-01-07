"""Correlation ID middleware for request tracking."""

import contextvars
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable for correlation ID
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id",
    default="",
)

CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str:
    """Get the current correlation ID from context.

    Returns:
        Current correlation ID or empty string.
    """
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to inject correlation ID into requests."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with correlation ID.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response with correlation ID header.
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid4())

        # Set in context
        token = correlation_id_ctx.set(correlation_id)

        try:
            # Store in request state for access in handlers
            request.state.correlation_id = correlation_id

            # Process request
            response = await call_next(request)

            # Add correlation ID to response
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            # Reset context
            correlation_id_ctx.reset(token)

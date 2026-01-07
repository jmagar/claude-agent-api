"""Structured request logging middleware."""

import logging
import time
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

if TYPE_CHECKING:
    import starlette.types

from apps.api.middleware.correlation import get_correlation_id

LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logging(log_level: str = "INFO", log_json: bool = True) -> None:
    """Configure structlog for the application.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_json: Whether to use JSON format.
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if log_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name.

    Returns:
        Bound logger instance.
    """
    logger: structlog.BoundLogger = structlog.get_logger(name)
    return logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""

    def __init__(
        self,
        app: "starlette.types.ASGIApp",
        skip_paths: list[str] | None = None,
    ) -> None:
        """Initialize middleware.

        Args:
            app: ASGI application.
            skip_paths: Paths to skip logging for.
        """
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/metrics"]
        self.logger = get_logger("http")

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with logging.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response.
        """
        # Skip logging for certain paths
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Start timer
        start_time = time.perf_counter()

        # Get correlation ID
        correlation_id = get_correlation_id()

        # Bind context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            client_ip=self._get_client_ip(request),
        )

        # Log request start
        self.logger.info(
            "request_started",
            query_params=str(request.query_params),
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            self.logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log error
            self.logger.error(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2),
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request.

        Args:
            request: Incoming request.

        Returns:
            Client IP address.
        """
        # Check for forwarded header (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Fall back to direct connection
        if request.client:
            return request.client.host
        return "unknown"

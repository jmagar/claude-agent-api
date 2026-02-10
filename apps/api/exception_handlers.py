"""Exception handlers for FastAPI application.

Provides centralized error handling for all application routes,
with OpenAI-compatible error format support for /v1/* endpoints.
"""

from collections.abc import Mapping, Sequence

import structlog
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from apps.api.config import Settings
from apps.api.exceptions import APIError, RequestTimeoutError
from apps.api.services.openai.errors import ErrorTranslator

logger = structlog.get_logger(__name__)


def _serialize_validation_errors(
    errors: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Convert Pydantic errors to JSON-serializable format.

    Args:
        errors: List of error dicts from Pydantic validation.

    Returns:
        List of sanitized error dicts safe for JSON serialization.
    """
    serialized: list[dict[str, object]] = []
    for error in errors:
        loc = error.get("loc")
        # Build serialized_error with explicit type annotation
        serialized_error: dict[str, object] = {
            "loc": list(loc) if isinstance(loc, (list, tuple)) else [],
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", "")),
        }
        # Convert ctx to strings if present (ValueError objects not JSON serializable)
        ctx = error.get("ctx")
        if isinstance(ctx, dict):
            ctx_dict: dict[str, str] = {str(k): str(v) for k, v in ctx.items()}
            serialized_error["ctx"] = ctx_dict
        serialized.append(serialized_error)
    return serialized


def _map_http_exception_code(status_code: int) -> str:
    """Map HTTPException status codes to API error codes.

    Args:
        status_code: HTTP status code.

    Returns:
        API error code string.
    """
    status_map = {
        400: "VALIDATION_ERROR",
        401: "AUTHENTICATION_ERROR",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    return status_map.get(status_code, "HTTP_ERROR")


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle API errors.

    For OpenAI-compatible endpoints (/v1/*), translates errors to OpenAI format.
    For native endpoints (/api/v1/*), uses standard API error format.

    Args:
        request: FastAPI request object.
        exc: API error exception.

    Returns:
        JSON response with error details.
    """
    # Check if this is an OpenAI endpoint
    if request.url.path.startswith("/v1/"):
        # Translate to OpenAI error format
        openai_error = ErrorTranslator.translate(exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=openai_error,
        )

    # Use standard API error format for native endpoints
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle FastAPI request validation errors.

    Pydantic validation before route handler.

    For OpenAI endpoints (/v1/*), converts to OpenAI error format with 400 status.
    For native endpoints, uses FastAPI's default 422 format.

    Args:
        request: FastAPI request object.
        exc: Request validation error.

    Returns:
        JSON response with validation error details.
    """
    # Check if this is an OpenAI endpoint
    if request.url.path.startswith("/v1/"):
        # Extract first error message for simplicity
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        error_msg = first_error.get("msg", "Validation failed")
        field = ".".join(str(loc) for loc in first_error.get("loc", []))

        # Create APIError with 400 status for OpenAI translation
        api_error = APIError(
            message=error_msg,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {},
        )

        # Translate to OpenAI error format
        openai_error = ErrorTranslator.translate(api_error)
        return JSONResponse(
            status_code=400,
            content=openai_error,
        )

    # For native endpoints, use FastAPI default format (422)
    return JSONResponse(
        status_code=422,
        content={"detail": _serialize_validation_errors(exc.errors())},
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors raised in route handlers.

    For OpenAI endpoints (/v1/*), converts to OpenAI error format with 400 status.
    For native endpoints, uses FastAPI's default 422 format.

    Args:
        request: FastAPI request object.
        exc: Pydantic validation error.

    Returns:
        JSON response with validation error details.
    """
    # Check if this is an OpenAI endpoint
    if request.url.path.startswith("/v1/"):
        # Extract first error message for simplicity
        errors = exc.errors()
        if errors:
            first_error = errors[0]
            error_msg = str(first_error.get("msg", "Validation failed"))
            field = ".".join(str(loc) for loc in first_error.get("loc", []))
        else:
            error_msg = "Validation failed"
            field = ""

        # Create APIError with 400 status for OpenAI translation
        api_error = APIError(
            message=error_msg,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {},
        )

        # Translate to OpenAI error format
        openai_error = ErrorTranslator.translate(api_error)
        return JSONResponse(
            status_code=400,
            content=openai_error,
        )

    # For native endpoints, use FastAPI default format (422)
    return JSONResponse(
        status_code=422,
        content={"detail": _serialize_validation_errors(exc.errors())},
    )


def create_timeout_handler(settings: Settings):
    """Create timeout exception handler with settings closure.

    Args:
        settings: Application settings for timeout configuration.

    Returns:
        Timeout exception handler function.
    """

    async def timeout_exception_handler(
        _request: Request,
        exc: TimeoutError,
    ) -> JSONResponse:
        """Handle timeout exceptions.

        Args:
            _request: FastAPI request (unused).
            exc: Timeout error.

        Returns:
            JSON response with timeout error details.
        """
        # Use exception message if available, otherwise default
        message = str(exc) if str(exc) else "Request timed out"
        timeout_error = RequestTimeoutError(
            message=message,
            timeout_seconds=settings.request_timeout,
            operation="request",
        )
        # Log for debugging
        logger.warning(
            "Request timeout",
            timeout_seconds=settings.request_timeout,
            error=str(exc),
        )
        return JSONResponse(
            status_code=timeout_error.status_code,
            content=timeout_error.to_dict(),
        )

    return timeout_exception_handler


def create_general_exception_handler(settings: Settings):
    """Create general exception handler with settings closure.

    Args:
        settings: Application settings for debug mode.

    Returns:
        General exception handler function.
    """

    async def general_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions.

        Args:
            _request: FastAPI request (unused).
            exc: Unexpected exception.

        Returns:
            JSON response with generic error message.
        """
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"type": type(exc).__name__} if settings.debug else {},
                }
            },
        )

    return general_exception_handler


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle HTTPException (used by models endpoint).

    For OpenAI endpoints (/v1/*), converts to OpenAI error format.
    For native endpoints, uses FastAPI's default format.

    Args:
        request: FastAPI request object.
        exc: HTTP exception.

    Returns:
        JSON response with HTTP error details.
    """
    # Check if this is an OpenAI endpoint
    if request.url.path.startswith("/v1/"):
        # Convert HTTPException to APIError for translation
        api_error = APIError(
            message=str(exc.detail),
            code=_map_http_exception_code(exc.status_code),
            status_code=exc.status_code,
        )

        # Translate to OpenAI error format
        openai_error = ErrorTranslator.translate(api_error)
        return JSONResponse(
            status_code=exc.status_code,
            content=openai_error,
        )

    # Use FastAPI default format for native endpoints
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


def register_exception_handlers(app, settings: Settings) -> None:
    """Register all exception handlers on the FastAPI app.

    Args:
        app: FastAPI application instance.
        settings: Application settings for handler configuration.
    """
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_error_handler)
    app.add_exception_handler(TimeoutError, create_timeout_handler(settings))
    app.add_exception_handler(Exception, create_general_exception_handler(settings))
    app.add_exception_handler(HTTPException, http_exception_handler)

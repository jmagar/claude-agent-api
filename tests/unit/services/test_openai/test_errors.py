"""Unit tests for OpenAI ErrorTranslator service."""

from typing import TYPE_CHECKING

import pytest

from apps.api.exceptions.base import APIError
from apps.api.services.openai.errors import ErrorTranslator

if TYPE_CHECKING:
    from apps.api.schemas.openai.responses import OpenAIError


class TestErrorTranslator:
    """Test suite for ErrorTranslator service."""

    def test_translate_401_to_authentication_error(self) -> None:
        """Status 401 should translate to authentication_error type."""
        error = APIError(
            message="Invalid API key",
            code="INVALID_API_KEY",
            status_code=401,
        )

        result: OpenAIError = ErrorTranslator.translate(error)

        assert result["error"]["type"] == "authentication_error"
        assert result["error"]["message"] == "Invalid API key"
        assert result["error"]["code"] == "INVALID_API_KEY"

    def test_translate_400_to_invalid_request(self) -> None:
        """Status 400 should translate to invalid_request_error type."""
        error = APIError(
            message="Missing required field",
            code="INVALID_REQUEST",
            status_code=400,
        )

        result: OpenAIError = ErrorTranslator.translate(error)

        assert result["error"]["type"] == "invalid_request_error"
        assert result["error"]["message"] == "Missing required field"
        assert result["error"]["code"] == "INVALID_REQUEST"

    def test_translate_429_to_rate_limit(self) -> None:
        """Status 429 should translate to rate_limit_exceeded type."""
        error = APIError(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )

        result: OpenAIError = ErrorTranslator.translate(error)

        assert result["error"]["type"] == "rate_limit_exceeded"
        assert result["error"]["message"] == "Rate limit exceeded"
        assert result["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    def test_translate_500_to_api_error(self) -> None:
        """Status 500 should translate to api_error type."""
        error = APIError(
            message="Internal server error",
            code="INTERNAL_ERROR",
            status_code=500,
        )

        result: OpenAIError = ErrorTranslator.translate(error)

        assert result["error"]["type"] == "api_error"
        assert result["error"]["message"] == "Internal server error"
        assert result["error"]["code"] == "INTERNAL_ERROR"

    def test_translate_403_to_permission_error(self) -> None:
        """Status 403 should translate to permission_error type."""
        error = APIError(
            message="Access denied",
            code="ACCESS_DENIED",
            status_code=403,
        )

        result: OpenAIError = ErrorTranslator.translate(error)

        assert result["error"]["type"] == "permission_error"
        assert result["error"]["message"] == "Access denied"
        assert result["error"]["code"] == "ACCESS_DENIED"

    def test_translate_preserves_message(self) -> None:
        """Error message should be preserved in the result."""
        custom_message = "This is a custom error message with details"
        error = APIError(
            message=custom_message,
            code="CUSTOM_ERROR",
            status_code=400,
        )

        result: OpenAIError = ErrorTranslator.translate(error)

        assert result["error"]["message"] == custom_message
        assert result["error"]["code"] == "CUSTOM_ERROR"


# Fixtures for mock APIError instances
@pytest.fixture
def auth_error() -> APIError:
    """Create a 401 authentication error."""
    return APIError(
        message="Authentication failed",
        code="AUTH_FAILED",
        status_code=401,
    )


@pytest.fixture
def bad_request_error() -> APIError:
    """Create a 400 bad request error."""
    return APIError(
        message="Bad request",
        code="BAD_REQUEST",
        status_code=400,
    )


@pytest.fixture
def rate_limit_error() -> APIError:
    """Create a 429 rate limit error."""
    return APIError(
        message="Too many requests",
        code="RATE_LIMIT",
        status_code=429,
    )


@pytest.fixture
def server_error() -> APIError:
    """Create a 500 server error."""
    return APIError(
        message="Server error",
        code="SERVER_ERROR",
        status_code=500,
    )

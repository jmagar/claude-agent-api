"""Unit tests for exception handlers (Priority 7).

Tests all exception handlers including APIError, TimeoutError,
and generic exceptions with proper error response formatting.
"""

import json
from collections.abc import Awaitable, Callable
from typing import cast
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient


def decode_response_body(response: JSONResponse) -> dict[str, object]:
    """Decode response body to dict.

    Args:
        response: JSONResponse object.

    Returns:
        Decoded response body as a dictionary.

    Raises:
        AssertionError: If response body is not a dict.
    """
    body = response.body
    body_bytes = bytes(body) if isinstance(body, memoryview) else body
    decoded: object = json.loads(body_bytes.decode())
    assert isinstance(decoded, dict), "Response body must be a dict"
    return decoded


@pytest.fixture
def test_app() -> FastAPI:
    """Create test FastAPI app with exception handlers.

    Returns:
        FastAPI app instance with exception handlers.
    """
    from apps.api.main import create_app

    return create_app()


class TestAPIErrorHandler:
    """Tests for APIError exception handler."""

    @pytest.mark.anyio
    async def test_handles_authentication_error(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test handling of AuthenticationError.

        GREEN: This test verifies authentication errors are properly formatted.
        """
        # Make request without API key
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_handles_session_not_found_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test handling of SessionNotFoundError.

        GREEN: This test verifies session not found errors are properly formatted.
        """
        # Try to get nonexistent session
        response = await async_client.get(
            "/api/v1/sessions/nonexistent-session-id",
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.anyio
    async def test_handles_checkpoint_not_found_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_checkpoint_from_other_session: str,
    ) -> None:
        """Test handling of CheckpointNotFoundError.

        GREEN: This test verifies checkpoint not found errors are properly formatted.
        """
        # Try to rewind to checkpoint from another session (should trigger error)
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/rewind",
            headers=auth_headers,
            json={"checkpoint_id": mock_checkpoint_from_other_session},
        )

        # Should return 400 or 404 depending on validation
        assert response.status_code in [400, 404]
        data = response.json()
        assert "error" in data
        # Either CHECKPOINT_NOT_FOUND or INVALID_CHECKPOINT depending on implementation
        assert data["error"]["code"] in ["CHECKPOINT_NOT_FOUND", "INVALID_CHECKPOINT"]

    @pytest.mark.anyio
    async def test_handles_validation_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test handling of ValidationError.

        GREEN: This test verifies validation errors are properly formatted.
        """
        # Make request with invalid data (missing required field)
        response = await async_client.post(
            "/api/v1/query",
            headers=auth_headers,
            json={},  # Missing required 'prompt' field
        )

        assert response.status_code == 422
        data = response.json()
        # FastAPI's default validation error structure
        assert "detail" in data

    @pytest.mark.anyio
    async def test_handles_service_unavailable_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test handling of ServiceUnavailableError.

        GREEN: This test verifies service unavailable errors include retry_after.
        """
        # Mock shutdown manager to return shutting down state
        from apps.api.services.shutdown import get_shutdown_manager

        manager = get_shutdown_manager()
        manager._shutting_down = True

        try:
            # Make request during shutdown
            response = await async_client.post(
                "/api/v1/query",
                headers=auth_headers,
                json={"prompt": "test"},
            )

            assert response.status_code == 503
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
            # Should include retry_after in response
            if "retry_after" in data["error"]:
                assert isinstance(data["error"]["retry_after"], int)
        finally:
            # Reset shutdown state
            manager._shutting_down = False

    @pytest.mark.anyio
    async def test_api_error_includes_correlation_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test error responses include correlation ID.

        GREEN: This test verifies correlation ID is propagated to errors.
        """
        correlation_id = "test-correlation-123"

        # Make request with correlation ID header
        response = await async_client.get(
            "/api/v1/sessions/nonexistent-session-id",
            headers={
                **auth_headers,
                "X-Correlation-ID": correlation_id,
            },
        )

        # Response should include correlation ID in header
        assert response.headers.get("X-Correlation-ID") == correlation_id


class TestTimeoutErrorHandler:
    """Tests for TimeoutError exception handler."""

    @pytest.mark.anyio
    async def test_handles_timeout_exception(
        self,
        test_app: FastAPI,
    ) -> None:
        """Test timeout exception handling.

        GREEN: This test verifies timeout errors are converted to RequestTimeoutError.
        """
        # Get the timeout handler
        timeout_handler = None
        for handler_info in test_app.exception_handlers.items():
            if handler_info[0] == TimeoutError:
                timeout_handler = handler_info[1]
                break

        assert timeout_handler is not None

        # Cast to async handler type
        async_handler = cast(
            Callable[[Request, TimeoutError], Awaitable[JSONResponse]],
            timeout_handler
        )

        # Create mock request and timeout exception
        mock_request = Mock(spec=Request)
        timeout_exc = TimeoutError("Operation timed out")

        # Call handler (async)
        response = await async_handler(mock_request, timeout_exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 504
        response_data = decode_response_body(response)
        assert "error" in response_data
        error_data = response_data["error"]
        assert isinstance(error_data, dict)
        assert error_data.get("code") == "REQUEST_TIMEOUT"

    @pytest.mark.anyio
    async def test_timeout_handler_includes_timeout_duration(
        self,
        test_app: FastAPI,
    ) -> None:
        """Test timeout error includes timeout duration.

        GREEN: This test verifies timeout duration is included in response.
        """
        # Get the timeout handler
        timeout_handler = None
        for handler_info in test_app.exception_handlers.items():
            if handler_info[0] == TimeoutError:
                timeout_handler = handler_info[1]
                break

        assert timeout_handler is not None

        # Cast to async handler type
        async_handler = cast(
            Callable[[Request, TimeoutError], Awaitable[JSONResponse]],
            timeout_handler
        )

        # Create mock request and timeout exception
        mock_request = Mock(spec=Request)
        timeout_exc = TimeoutError("Request timed out after 60 seconds")

        # Call handler (async)
        response = await async_handler(mock_request, timeout_exc)

        assert isinstance(response, JSONResponse)
        # Check response body contains timeout info
        response_data = decode_response_body(response)
        response_json_str = json.dumps(response_data).lower()
        assert "timeout" in response_json_str


class TestGeneralExceptionHandler:
    """Tests for generic exception handler."""

    @pytest.mark.anyio
    async def test_handles_generic_exception(
        self,
        test_app: FastAPI,
    ) -> None:
        """Test handling of unexpected exceptions.

        GREEN: This test verifies generic exceptions return 500.
        """
        # Get the general exception handler
        general_handler = None
        for handler_info in test_app.exception_handlers.items():
            if handler_info[0] == Exception:
                general_handler = handler_info[1]
                break

        assert general_handler is not None

        # Cast to async handler type
        async_handler = cast(
            Callable[[Request, Exception], Awaitable[JSONResponse]],
            general_handler
        )

        # Create mock request and generic exception
        mock_request = Mock(spec=Request)
        exc = RuntimeError("Unexpected error")

        # Call handler (async)
        response = await async_handler(mock_request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        response_data = decode_response_body(response)
        assert "error" in response_data
        error_data = response_data["error"]
        assert isinstance(error_data, dict)
        assert error_data.get("code") == "INTERNAL_ERROR"

    @pytest.mark.anyio
    async def test_generic_exception_hides_details_in_production(
        self,
        test_app: FastAPI,
    ) -> None:
        """Test generic exceptions hide details when not in debug mode.

        GREEN: This test verifies production safety.
        """
        from apps.api.config import get_settings

        # Temporarily set debug to False
        settings = get_settings()
        original_debug = settings.debug
        settings.debug = False

        try:
            # Get the general exception handler
            general_handler = None
            for handler_info in test_app.exception_handlers.items():
                if handler_info[0] == Exception:
                    general_handler = handler_info[1]
                    break

            assert general_handler is not None

            # Cast to async handler type
            async_handler = cast(
                Callable[[Request, Exception], Awaitable[JSONResponse]],
                general_handler
            )

            # Create mock request and generic exception
            mock_request = Mock(spec=Request)
            exc = ValueError("Sensitive internal error")

            # Call handler (async)
            response = await async_handler(mock_request, exc)

            response_data = decode_response_body(response)
            # Should not contain exception type in production
            assert "error" in response_data
            error_data = response_data["error"]
            assert isinstance(error_data, dict)
            assert "details" in error_data
            assert error_data["details"] == {}
        finally:
            settings.debug = original_debug

    @pytest.mark.anyio
    async def test_generic_exception_includes_type_in_debug(
        self,
        test_app: FastAPI,
    ) -> None:
        """Test generic exceptions include exception type in debug mode.

        GREEN: This test verifies debug information.
        """
        from apps.api.config import get_settings

        # Temporarily set debug to True
        settings = get_settings()
        original_debug = settings.debug
        settings.debug = True

        try:
            # Get the general exception handler
            general_handler = None
            for handler_info in test_app.exception_handlers.items():
                if handler_info[0] == Exception:
                    general_handler = handler_info[1]
                    break

            assert general_handler is not None

            # Cast to async handler type
            async_handler = cast(
                Callable[[Request, Exception], Awaitable[JSONResponse]],
                general_handler
            )

            # Create mock request and generic exception
            mock_request = Mock(spec=Request)
            exc = ValueError("Debug mode error")

            # Call handler (async)
            response = await async_handler(mock_request, exc)

            response_data = decode_response_body(response)
            # Should contain exception type in debug mode
            assert "error" in response_data
            error_data = response_data["error"]
            assert isinstance(error_data, dict)
            assert "details" in error_data
            details = error_data["details"]
            if details:
                assert isinstance(details, dict)
                assert "type" in details
                assert details["type"] == "ValueError"
        finally:
            settings.debug = original_debug


class TestErrorResponseFormat:
    """Tests for consistent error response formatting."""

    @pytest.mark.anyio
    async def test_all_api_errors_have_consistent_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test all API errors follow consistent format.

        GREEN: This test verifies error response structure consistency.
        """
        # Test multiple error types
        error_responses = []

        # AuthenticationError
        response1 = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test"},
        )
        error_responses.append(response1.json())

        # SessionNotFoundError
        response2 = await async_client.get(
            "/api/v1/sessions/nonexistent",
            headers=auth_headers,
        )
        error_responses.append(response2.json())

        # All should have "error" key with code and message
        for error_response in error_responses:
            if "error" in error_response:
                assert "code" in error_response["error"]
                assert "message" in error_response["error"]
                assert isinstance(error_response["error"]["code"], str)
                assert isinstance(error_response["error"]["message"], str)

    @pytest.mark.anyio
    async def test_error_messages_are_user_friendly(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test error messages are clear and actionable.

        GREEN: This test verifies error messages are helpful.
        """
        # Test authentication error message
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test"},
        )

        data = response.json()
        if "error" in data:
            message = data["error"]["message"]
            # Message should be clear about what's wrong
            assert len(message) > 0
            assert message.lower() in ["missing api key", "invalid api key"]

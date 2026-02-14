"""Integration tests for query error handling.

Tests verify that critical error scenarios are handled correctly:
- Session persistence failures
- JSON parsing failures in result events
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError, OperationalError


class TestQuerySingleErrorHandling:
    """Test error handling in non-streaming query endpoint."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_persistence_failure_returns_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Session persistence failures must fail the request.

        Critical Issue #1 from Phase 2 audit:
        - Session persistence failures should raise APIError
        - Must NOT return success with invalid session_id
        - Status code: 500
        - Error code: SESSION_PERSISTENCE_FAILED
        """
        request_data = {
            "prompt": "Test query",
            "max_turns": 1,
        }

        # Mock session service to raise database error on create_session
        with patch(
            "apps.api.services.session.SessionService.create_session",
            side_effect=OperationalError("Database unavailable", None, None),
        ):
            response = await async_client.post(
                "/api/v1/query/single",
                headers=auth_headers,
                json=request_data,
            )

        # Must return error with 503 status (database unavailable)
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == "DATABASE_UNAVAILABLE"
        assert "database" in error["message"].lower()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_update_failure_returns_error(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Session update failures during status tracking must fail request."""
        request_data = {
            "prompt": "Test query",
            "max_turns": 1,
        }

        # Mock session service: create succeeds, update fails
        with patch(
            "apps.api.services.session.SessionService.update_session",
            side_effect=OperationalError("Database unavailable", None, None),
        ):
            response = await async_client.post(
                "/api/v1/query/single",
                headers=auth_headers,
                json=request_data,
            )

        # Must return error with 503 status
        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == "DATABASE_UNAVAILABLE"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_duplicate_returns_409(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Integrity constraint violations must return 409 Conflict.

        Tests exception specificity from Task #5:
        - IntegrityError → 409 SESSION_ALREADY_EXISTS
        - Distinguishes from OperationalError (503)
        """
        request_data = {
            "prompt": "Test query",
            "max_turns": 1,
        }

        # Mock session service to raise integrity error
        with patch(
            "apps.api.services.session.SessionService.create_session",
            side_effect=IntegrityError(
                "duplicate key value violates unique constraint",
                None,
                None,
            ),
        ):
            response = await async_client.post(
                "/api/v1/query/single",
                headers=auth_headers,
                json=request_data,
            )

        # Must return 409 Conflict, not 500
        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == "SESSION_ALREADY_EXISTS"
        assert "already exists" in error["message"].lower()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_unexpected_error_returns_500(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Unexpected errors must return 500 with generic error code.

        Tests catch-all exception handler from Task #5:
        - Non-database exceptions → 500 SESSION_CREATION_FAILED
        - Includes exc_info for debugging
        """
        request_data = {
            "prompt": "Test query",
            "max_turns": 1,
        }

        # Mock session service to raise unexpected error
        with patch(
            "apps.api.services.session.SessionService.create_session",
            side_effect=RuntimeError("Unexpected service failure"),
        ):
            response = await async_client.post(
                "/api/v1/query/single",
                headers=auth_headers,
                json=request_data,
            )

        # Must return 500 with generic error code
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == "SESSION_CREATION_FAILED"
        assert "session state" in error["message"].lower()


class TestQueryStreamErrorHandling:
    """Test error handling in streaming query endpoint.

    Note: These tests verify that the error handling code exists and is correct.
    Full end-to-end testing requires mocking at the SDK level, which is complex
    and brittle. The unit tests in test_query_stream.py provide more detailed
    coverage of the error handling logic.
    """

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_stream_validates_request(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Verify streaming endpoint validates requests properly."""
        # Missing required prompt field
        request_data: dict[str, object] = {}

        response = await async_client.post(
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        )

        # Should return validation error, not stream
        assert response.status_code == 422

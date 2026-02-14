"""Unit tests for query stream event generator.

Tests verify error handling logic in QueryStreamEventGenerator:
- JSON parsing failure logging (Critical Issue #8)
- Session initialization error handling
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.routes.query_stream import QueryStreamEventGenerator
from apps.api.schemas.requests.query import QueryRequest


class TestQueryStreamEventGenerator:
    """Unit tests for QueryStreamEventGenerator error handling."""

    @pytest.mark.anyio
    async def test_track_event_metadata_logs_json_parse_failure(self) -> None:
        """Result event JSON parse failures must log with context.

        Critical Issue #8 from Phase 2 audit:
        - Must log with error_id="ERR_RESULT_PARSE_FAILED"
        - Must include: session_id, error, event_data (truncated)
        """
        # Create generator with mocked dependencies
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        query = QueryRequest(prompt="test", max_turns=1)
        agent_service = MagicMock()
        session_service = MagicMock()

        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=agent_service,
            session_service=session_service,
        )

        # Set session_id so it appears in logs
        generator.session_id = "test-session-123"

        # Track malformed result event with mock logger
        with patch("apps.api.routes.query_stream.logger") as mock_logger:
            malformed_json = "INVALID JSON{malformed"
            generator._track_event_metadata("result", malformed_json)

            # Verify error was logged
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args

            # Verify log message
            assert call_args[0][0] == "failed_to_parse_result_event"

            # Verify required fields in kwargs
            kwargs = call_args[1]
            assert "session_id" in kwargs
            assert kwargs["session_id"] == "test-session-123"
            assert "error" in kwargs
            assert "Expecting value" in kwargs["error"]  # JSON decode error message
            assert "event_data" in kwargs
            assert (
                kwargs["event_data"] == malformed_json[:500]
            )  # Truncated to 500 chars
            assert "error_id" in kwargs
            assert kwargs["error_id"] == "ERR_RESULT_PARSE_FAILED"

    @pytest.mark.anyio
    async def test_track_event_metadata_parses_valid_json(self) -> None:
        """Valid result events should parse without errors."""
        mock_request = MagicMock()
        query = QueryRequest(prompt="test", max_turns=1)
        agent_service = MagicMock()
        session_service = MagicMock()

        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=agent_service,
            session_service=session_service,
        )

        # Track valid result event
        with patch("apps.api.routes.query_stream.logger") as mock_logger:
            valid_json = json.dumps({"turns": 3, "total_cost_usd": 0.05})
            generator._track_event_metadata("result", valid_json)

            # Verify NO error was logged
            mock_logger.error.assert_not_called()

            # Verify metadata was extracted
            assert generator.num_turns == 3
            assert generator.total_cost_usd == 0.05

    @pytest.mark.anyio
    async def test_handle_init_event_logs_parse_failure(self) -> None:
        """Init event parse failures must log and emit error event."""
        mock_request = MagicMock()
        query = QueryRequest(prompt="test", max_turns=1)
        agent_service = MagicMock()
        session_service = MagicMock()

        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=agent_service,
            session_service=session_service,
        )

        # Try to handle malformed init event
        with (
            patch("apps.api.routes.query_stream.logger") as mock_logger,
            pytest.raises(json.JSONDecodeError),
        ):
            await generator._handle_init_event("INVALID JSON")

        # Verify error was logged
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert call_args[0][0] == "Failed to parse init event"

        # Verify error event was queued for client
        error_event = await generator.event_queue.get()
        assert error_event is not None
        assert error_event["event"] == "error"

        # Parse error data
        error_data = json.loads(error_event["data"])
        assert "error" in error_data
        assert "Session initialization failed" in error_data["error"]

    @pytest.mark.anyio
    async def test_track_event_metadata_increments_turns(self) -> None:
        """Message events should increment turn counter."""
        mock_request = MagicMock()
        query = QueryRequest(prompt="test", max_turns=1)
        agent_service = MagicMock()
        session_service = MagicMock()

        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=agent_service,
            session_service=session_service,
        )

        # Track message events
        assert generator.num_turns == 0
        generator._track_event_metadata("message", "{}")
        assert generator.num_turns == 1
        generator._track_event_metadata("message", "{}")
        assert generator.num_turns == 2

    @pytest.mark.anyio
    async def test_track_event_metadata_sets_error_flag(self) -> None:
        """Error events should set is_error flag."""
        mock_request = MagicMock()
        query = QueryRequest(prompt="test", max_turns=1)
        agent_service = MagicMock()
        session_service = MagicMock()

        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=agent_service,
            session_service=session_service,
        )

        # Track error event
        assert generator.is_error is False
        generator._track_event_metadata("error", json.dumps({"error": "test"}))
        assert generator.is_error is True

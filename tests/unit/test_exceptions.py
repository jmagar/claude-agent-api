"""Unit tests for exception classes."""

from apps.api.exceptions import (
    AgentError,
    APIError,
    AuthenticationError,
    CacheError,
    CheckpointNotFoundError,
    DatabaseError,
    HookError,
    InvalidCheckpointError,
    RateLimitError,
    RequestTimeoutError,
    ServiceUnavailableError,
    SessionCompletedError,
    SessionLockedError,
    SessionNotFoundError,
    StructuredOutputValidationError,
    ToolNotAllowedError,
    ValidationError,
)


class TestAPIError:
    """Tests for base APIError class."""

    def test_default_values(self) -> None:
        """Test default error values."""
        error = APIError("Test error")

        assert error.message == "Test error"
        assert error.code == "INTERNAL_ERROR"
        assert error.status_code == 500
        assert error.details == {}

    def test_custom_values(self) -> None:
        """Test custom error values."""
        error = APIError(
            message="Custom error",
            code="CUSTOM_CODE",
            status_code=400,
            details={"key": "value"},
        )

        assert error.message == "Custom error"
        assert error.code == "CUSTOM_CODE"
        assert error.status_code == 400
        assert error.details == {"key": "value"}

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        error = APIError(
            message="Test error",
            code="TEST_CODE",
            status_code=400,
            details={"field": "value"},
        )

        result = error.to_dict()

        assert result == {
            "error": {
                "code": "TEST_CODE",
                "message": "Test error",
                "details": {"field": "value"},
            }
        }

    def test_str_representation(self) -> None:
        """Test string representation."""
        error = APIError("Test message")
        assert str(error) == "Test message"

    def test_repr(self) -> None:
        """Test repr for debugging."""
        error = APIError(
            message="Test error",
            code="TEST_CODE",
            status_code=400,
        )

        result = repr(error)

        assert result == "APIError(message='Test error', code='TEST_CODE', status_code=400)"


class TestSessionNotFoundError:
    """Tests for SessionNotFoundError."""

    def test_error_details(self) -> None:
        """Test error contains session ID."""
        error = SessionNotFoundError("session-123")

        assert error.status_code == 404
        assert error.code == "SESSION_NOT_FOUND"
        assert "session-123" in error.message
        assert error.details["session_id"] == "session-123"


class TestSessionLockedError:
    """Tests for SessionLockedError."""

    def test_error_details(self) -> None:
        """Test error contains session ID."""
        error = SessionLockedError("session-456")

        assert error.status_code == 409
        assert error.code == "SESSION_LOCKED"
        assert "session-456" in error.message
        assert error.details["session_id"] == "session-456"


class TestSessionCompletedError:
    """Tests for SessionCompletedError."""

    def test_error_details(self) -> None:
        """Test error contains session ID and status."""
        error = SessionCompletedError("session-789", "completed")

        assert error.status_code == 400
        assert error.code == "SESSION_COMPLETED"
        assert "session-789" in error.message
        assert "completed" in error.message
        assert error.details["session_id"] == "session-789"
        assert error.details["status"] == "completed"


class TestValidationError:
    """Tests for ValidationError."""

    def test_without_field(self) -> None:
        """Test validation error without field."""
        error = ValidationError("Invalid input")

        assert error.status_code == 422
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"
        assert error.details == {}

    def test_with_field(self) -> None:
        """Test validation error with field."""
        error = ValidationError("Invalid email", field="email")

        assert error.status_code == 422
        assert error.code == "VALIDATION_ERROR"
        assert error.details["field"] == "email"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = AuthenticationError()

        assert error.status_code == 401
        assert error.code == "AUTHENTICATION_ERROR"
        assert "API key" in error.message

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = AuthenticationError("Token expired")

        assert error.message == "Token expired"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_without_retry_after(self) -> None:
        """Test rate limit error without retry info."""
        error = RateLimitError()

        assert error.status_code == 429
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.details == {}

    def test_with_retry_after(self) -> None:
        """Test rate limit error with retry info."""
        error = RateLimitError(retry_after=60)

        assert error.status_code == 429
        assert error.details["retry_after"] == 60

    def test_with_zero_retry_after(self) -> None:
        """Test rate limit error with zero retry info (immediate retry)."""
        error = RateLimitError(retry_after=0)

        assert error.status_code == 429
        assert error.details["retry_after"] == 0


class TestToolNotAllowedError:
    """Tests for ToolNotAllowedError."""

    def test_error_details(self) -> None:
        """Test error contains tool info."""
        error = ToolNotAllowedError("Bash", ["Read", "Write"])

        assert error.status_code == 400
        assert error.code == "TOOL_NOT_ALLOWED"
        assert "Bash" in error.message
        assert error.details["tool_name"] == "Bash"
        assert error.details["allowed_tools"] == ["Read", "Write"]


class TestCheckpointNotFoundError:
    """Tests for CheckpointNotFoundError."""

    def test_error_details(self) -> None:
        """Test error contains checkpoint ID."""
        error = CheckpointNotFoundError("checkpoint-abc")

        assert error.status_code == 404
        assert error.code == "CHECKPOINT_NOT_FOUND"
        assert "checkpoint-abc" in error.message
        assert error.details["checkpoint_id"] == "checkpoint-abc"


class TestInvalidCheckpointError:
    """Tests for InvalidCheckpointError."""

    def test_error_details(self) -> None:
        """Test error contains checkpoint and session IDs."""
        error = InvalidCheckpointError("cp-123", "sess-456")

        assert error.status_code == 400
        assert error.code == "INVALID_CHECKPOINT"
        assert error.details["checkpoint_id"] == "cp-123"
        assert error.details["session_id"] == "sess-456"

    def test_with_custom_reason(self) -> None:
        """Test error with custom reason."""
        error = InvalidCheckpointError("cp-123", "sess-456", reason="Checkpoint already restored")

        assert error.message == "Checkpoint already restored"


class TestHookError:
    """Tests for HookError."""

    def test_without_webhook_url(self) -> None:
        """Test hook error without webhook URL."""
        error = HookError("PreToolUse", "Webhook timeout")

        assert error.status_code == 502
        assert error.code == "HOOK_ERROR"
        assert error.message == "Webhook timeout"
        assert error.details["hook_event"] == "PreToolUse"
        assert "webhook_url" not in error.details

    def test_with_different_event(self) -> None:
        """Test hook error with different event type."""
        error = HookError(
            "PostToolUse",
            "Connection refused",
        )

        assert error.status_code == 502
        assert error.details["hook_event"] == "PostToolUse"
        # webhook_url intentionally excluded to prevent leaking sensitive info
        assert "webhook_url" not in error.details


class TestAgentError:
    """Tests for AgentError."""

    def test_without_original_error(self) -> None:
        """Test agent error without original error."""
        error = AgentError("Agent crashed")

        assert error.status_code == 500
        assert error.code == "AGENT_ERROR"
        assert error.message == "Agent crashed"
        assert error.details == {}

    def test_with_original_error(self) -> None:
        """Test agent error with original error."""
        error = AgentError("Agent failed", original_error="CLI process exited with 1")

        assert error.details["original_error"] == "CLI process exited with 1"


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = DatabaseError()

        assert error.status_code == 500
        assert error.code == "DATABASE_ERROR"
        assert "Database" in error.message


class TestCacheError:
    """Tests for CacheError."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = CacheError()

        assert error.status_code == 500
        assert error.code == "CACHE_ERROR"
        assert "Cache" in error.message


class TestStructuredOutputValidationError:
    """Tests for StructuredOutputValidationError (US8, T094)."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = StructuredOutputValidationError()

        assert error.status_code == 422
        assert error.code == "STRUCTURED_OUTPUT_VALIDATION_ERROR"
        assert "validation failed" in error.message.lower()
        assert error.details == {}

    def test_with_validation_errors(self) -> None:
        """Test error with validation error details."""
        error = StructuredOutputValidationError(
            message="Output does not match schema",
            validation_errors=[
                "Required field 'name' is missing",
                "Field 'age' expected integer, got string",
            ],
        )

        assert error.status_code == 422
        assert error.code == "STRUCTURED_OUTPUT_VALIDATION_ERROR"
        assert error.message == "Output does not match schema"
        assert error.details["validation_errors"] == [
            "Required field 'name' is missing",
            "Field 'age' expected integer, got string",
        ]

    def test_with_schema_type(self) -> None:
        """Test error with schema type information."""
        error = StructuredOutputValidationError(
            message="Invalid JSON output",
            schema_type="json_schema",
        )

        assert error.details["schema_type"] == "json_schema"

    def test_with_all_details(self) -> None:
        """Test error with all detail fields."""
        error = StructuredOutputValidationError(
            message="Schema validation failed",
            validation_errors=["Type mismatch at $.data.items[0]"],
            schema_type="json_schema",
        )

        assert error.status_code == 422
        assert error.code == "STRUCTURED_OUTPUT_VALIDATION_ERROR"
        assert error.details["validation_errors"] == ["Type mismatch at $.data.items[0]"]
        assert error.details["schema_type"] == "json_schema"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        error = StructuredOutputValidationError(
            message="Output validation failed",
            validation_errors=["Missing required field"],
            schema_type="json_schema",
        )

        result = error.to_dict()

        assert result == {
            "error": {
                "code": "STRUCTURED_OUTPUT_VALIDATION_ERROR",
                "message": "Output validation failed",
                "details": {
                    "validation_errors": ["Missing required field"],
                    "schema_type": "json_schema",
                },
            }
        }


class TestRequestTimeoutError:
    """Tests for RequestTimeoutError (T125)."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = RequestTimeoutError()

        assert error.status_code == 504
        assert error.code == "REQUEST_TIMEOUT"
        assert "timed out" in error.message.lower()
        assert error.details == {}

    def test_with_timeout_seconds(self) -> None:
        """Test error with timeout seconds."""
        error = RequestTimeoutError(
            message="Query timed out",
            timeout_seconds=300,
        )

        assert error.status_code == 504
        assert error.message == "Query timed out"
        assert error.details["timeout_seconds"] == 300

    def test_with_operation(self) -> None:
        """Test error with operation information."""
        error = RequestTimeoutError(
            message="Operation timed out",
            operation="agent_query",
        )

        assert error.details["operation"] == "agent_query"

    def test_with_all_details(self) -> None:
        """Test error with all detail fields."""
        error = RequestTimeoutError(
            message="Request exceeded timeout limit",
            timeout_seconds=120,
            operation="stream_query",
        )

        assert error.status_code == 504
        assert error.code == "REQUEST_TIMEOUT"
        assert error.details["timeout_seconds"] == 120
        assert error.details["operation"] == "stream_query"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        error = RequestTimeoutError(
            message="Timeout occurred",
            timeout_seconds=60,
            operation="query",
        )

        result = error.to_dict()

        assert result == {
            "error": {
                "code": "REQUEST_TIMEOUT",
                "message": "Timeout occurred",
                "details": {
                    "timeout_seconds": 60,
                    "operation": "query",
                },
            }
        }


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError (T125)."""

    def test_default_message(self) -> None:
        """Test default error message."""
        error = ServiceUnavailableError()

        assert error.status_code == 503
        assert error.code == "SERVICE_UNAVAILABLE"
        assert "unavailable" in error.message.lower()
        assert error.details == {}

    def test_with_retry_after(self) -> None:
        """Test error with retry-after information."""
        error = ServiceUnavailableError(
            message="Service under maintenance",
            retry_after=300,
        )

        assert error.status_code == 503
        assert error.message == "Service under maintenance"
        assert error.details["retry_after"] == 300

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = ServiceUnavailableError(message="System is shutting down")

        assert error.message == "System is shutting down"
        assert error.details == {}

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        error = ServiceUnavailableError(
            message="Maintenance in progress",
            retry_after=120,
        )

        result = error.to_dict()

        assert result == {
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Maintenance in progress",
                "details": {
                    "retry_after": 120,
                },
            }
        }

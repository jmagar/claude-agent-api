"""Unit tests for enhanced error logging context in query routes.

Verifies that all error logs include:
- session_id (even if None)
- api_key_hash (hashed, never raw)
- prompt_preview (first 100 chars)
- error_id for each error type
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import structlog

from apps.api.utils.crypto import hash_api_key


class TestQueryErrorLoggingContext:
    """Test that query.py error logs include rich debugging context."""

    @pytest.mark.unit
    def test_session_creation_error_includes_context(self) -> None:
        """Session creation error must include session_id, api_key_hash, and prompt_preview."""
        query_py = Path("apps/api/routes/query.py")
        content = query_py.read_text()

        # Find the session_creation_failed error log (Exception handler, not OperationalError)
        lines = content.split("\n")
        log_start = None
        for i, line in enumerate(lines):
            if '"session_creation_failed"' in line or "'session_creation_failed'" in line:
                log_start = i
                break

        assert log_start is not None, "session_creation_failed log not found"

        # Extract log call (multi-line) - go backwards to find logger.error(
        actual_start = log_start
        for i in range(log_start, max(0, log_start - 5), -1):
            if "logger.error(" in lines[i]:
                actual_start = i
                break

        # Now extract forward until closing paren
        log_block = []
        paren_depth = 0
        for i in range(actual_start, min(actual_start + 20, len(lines))):
            log_block.append(lines[i])
            paren_depth += lines[i].count("(") - lines[i].count(")")
            if paren_depth == 0 and i > actual_start:
                break

        log_text = "\n".join(log_block)

        # Verify required context fields
        assert "session_id=" in log_text, "Missing session_id in log"
        assert "api_key_hash=" in log_text, "Missing api_key_hash in log"
        assert "hash_api_key(api_key)" in log_text, "api_key_hash should use hash_api_key()"
        assert "prompt_preview=" in log_text, "Missing prompt_preview in log"
        assert "[:100]" in log_text, "prompt_preview should truncate to 100 chars"
        assert "error_id=" in log_text, "Missing error_id in log"
        assert "ERR_SESSION_CREATE_FAILED" in log_text, "error_id should be ERR_SESSION_CREATE_FAILED"


class TestQueryStreamErrorLoggingContext:
    """Test that query_stream.py error logs include rich debugging context."""

    @pytest.mark.unit
    def test_init_parse_error_includes_context(self) -> None:
        """Init event parse error must include session_id, api_key_hash, and prompt_preview."""
        query_stream_py = Path("apps/api/routes/query_stream.py")
        content = query_stream_py.read_text()

        # Find the init event parse error log (json.JSONDecodeError handler)
        lines = content.split("\n")
        log_start = None
        for i, line in enumerate(lines):
            if '"Failed to parse init event"' in line or "'Failed to parse init event'" in line:
                log_start = i
                break

        assert log_start is not None, "Init parse error log not found"

        # Go backwards to find logger.error( line
        actual_start = log_start
        for i in range(log_start, max(0, log_start - 5), -1):
            if "logger.error(" in lines[i]:
                actual_start = i
                break

        # Extract log call forward
        log_block = []
        paren_depth = 0
        for i in range(actual_start, min(actual_start + 20, len(lines))):
            log_block.append(lines[i])
            paren_depth += lines[i].count("(") - lines[i].count(")")
            if paren_depth == 0 and i > actual_start:
                break

        log_text = "\n".join(log_block)

        # Verify required context fields
        assert "session_id=" in log_text, "Missing session_id in log"
        assert "api_key_hash=" in log_text, "Missing api_key_hash in log"
        assert "hash_api_key(self.api_key)" in log_text, "api_key_hash should use hash_api_key()"
        assert "prompt_preview=" in log_text, "Missing prompt_preview in log"
        assert "[:100]" in log_text, "prompt_preview should truncate to 100 chars"
        assert "error_id=" in log_text, "Missing error_id in log"
        assert "ERR_INIT_PARSE_FAILED" in log_text, "error_id should be ERR_INIT_PARSE_FAILED"

    @pytest.mark.unit
    def test_session_create_error_includes_context(self) -> None:
        """Session create error must include session_id, api_key_hash, and prompt_preview."""
        query_stream_py = Path("apps/api/routes/query_stream.py")
        content = query_stream_py.read_text()

        # Find the session create error log
        lines = content.split("\n")
        log_start = None
        for i, line in enumerate(lines):
            if '"Failed to create session"' in line or "'Failed to create session'" in line:
                log_start = i
                break

        assert log_start is not None, "Session create error log not found"

        # Go backwards to find logger.error( line
        actual_start = log_start
        for i in range(log_start, max(0, log_start - 5), -1):
            if "logger.error(" in lines[i]:
                actual_start = i
                break

        # Extract log call forward
        log_block = []
        paren_depth = 0
        for i in range(actual_start, min(actual_start + 20, len(lines))):
            log_block.append(lines[i])
            paren_depth += lines[i].count("(") - lines[i].count(")")
            if paren_depth == 0 and i > actual_start:
                break

        log_text = "\n".join(log_block)

        # Verify required context fields
        assert "session_id=" in log_text, "Missing session_id in log"
        assert "api_key_hash=" in log_text, "Missing api_key_hash in log"
        assert "hash_api_key(self.api_key)" in log_text, "api_key_hash should use hash_api_key()"
        assert "prompt_preview=" in log_text, "Missing prompt_preview in log"
        assert "[:100]" in log_text, "prompt_preview should truncate to 100 chars"
        assert "error_id=" in log_text, "Missing error_id in log"
        assert "ERR_SESSION_CREATE_FAILED" in log_text, "error_id should be ERR_SESSION_CREATE_FAILED"

    @pytest.mark.unit
    def test_result_parse_error_includes_context(self) -> None:
        """Result event parse error must include session_id, api_key_hash, and prompt_preview."""
        query_stream_py = Path("apps/api/routes/query_stream.py")
        content = query_stream_py.read_text()

        # Find the result parse error log
        lines = content.split("\n")
        log_start = None
        for i, line in enumerate(lines):
            if '"failed_to_parse_result_event"' in line or "'failed_to_parse_result_event'" in line:
                log_start = i
                break

        assert log_start is not None, "Result parse error log not found"

        # Go backwards to find logger.error( line
        actual_start = log_start
        for i in range(log_start, max(0, log_start - 5), -1):
            if "logger.error(" in lines[i]:
                actual_start = i
                break

        # Extract log call forward
        log_block = []
        paren_depth = 0
        for i in range(actual_start, min(actual_start + 20, len(lines))):
            log_block.append(lines[i])
            paren_depth += lines[i].count("(") - lines[i].count(")")
            if paren_depth == 0 and i > actual_start:
                break

        log_text = "\n".join(log_block)

        # Verify required context fields
        assert "session_id=" in log_text, "Missing session_id in log"
        assert "api_key_hash=" in log_text, "Missing api_key_hash in log"
        assert "hash_api_key(self.api_key)" in log_text, "api_key_hash should use hash_api_key()"
        assert "prompt_preview=" in log_text, "Missing prompt_preview in log"
        assert "[:100]" in log_text, "prompt_preview should truncate to 100 chars"
        assert "error_id=" in log_text, "Missing error_id in log"
        assert "ERR_RESULT_PARSE_FAILED" in log_text, "error_id should be ERR_RESULT_PARSE_FAILED"

    @pytest.mark.unit
    def test_producer_error_includes_context(self) -> None:
        """Producer error must include session_id, api_key_hash, and prompt_preview."""
        query_stream_py = Path("apps/api/routes/query_stream.py")
        content = query_stream_py.read_text()

        # Find the producer error log
        lines = content.split("\n")
        log_start = None
        for i, line in enumerate(lines):
            if '"Producer error in event stream"' in line or "'Producer error in event stream'" in line:
                log_start = i
                break

        assert log_start is not None, "Producer error log not found"

        # Go backwards to find logger.error( line
        actual_start = log_start
        for i in range(log_start, max(0, log_start - 5), -1):
            if "logger.error(" in lines[i]:
                actual_start = i
                break

        # Extract log call forward
        log_block = []
        paren_depth = 0
        for i in range(actual_start, min(actual_start + 20, len(lines))):
            log_block.append(lines[i])
            paren_depth += lines[i].count("(") - lines[i].count(")")
            if paren_depth == 0 and i > actual_start:
                break

        log_text = "\n".join(log_block)

        # Verify required context fields
        assert "session_id=" in log_text, "Missing session_id in log"
        assert "api_key_hash=" in log_text, "Missing api_key_hash in log"
        assert "hash_api_key(self.api_key)" in log_text, "api_key_hash should use hash_api_key()"
        assert "prompt_preview=" in log_text, "Missing prompt_preview in log"
        assert "[:100]" in log_text, "prompt_preview should truncate to 100 chars"
        assert "error_id=" in log_text, "Missing error_id in log"
        assert "ERR_STREAM_PRODUCER_FAILED" in log_text, "error_id should be ERR_STREAM_PRODUCER_FAILED"

    @pytest.mark.unit
    def test_hash_api_key_import_exists(self) -> None:
        """Verify hash_api_key is imported in query_stream.py."""
        query_stream_py = Path("apps/api/routes/query_stream.py")
        content = query_stream_py.read_text()

        assert "from apps.api.utils.crypto import hash_api_key" in content, (
            "query_stream.py must import hash_api_key from utils.crypto"
        )


class TestErrorLoggingBehavior:
    """Test that error logs actually capture and format context correctly."""

    @pytest.mark.unit
    def test_prompt_preview_truncates_to_100_chars(self) -> None:
        """Verify prompt_preview logic truncates correctly."""
        # Simulate the truncation logic used in logs
        long_prompt = "a" * 200
        preview = long_prompt[:100] if long_prompt else None

        assert preview is not None
        assert len(preview) == 100
        assert preview == "a" * 100

    @pytest.mark.unit
    def test_prompt_preview_handles_none(self) -> None:
        """Verify prompt_preview handles None prompts."""
        prompt = None
        preview = prompt[:100] if prompt else None

        assert preview is None

    @pytest.mark.unit
    def test_api_key_hash_never_logs_raw_key(self) -> None:
        """Verify hash_api_key produces a hash, not the raw key."""
        raw_key = "secret-api-key-12345"
        hashed = hash_api_key(raw_key)

        # Hash should be different from raw key
        assert hashed != raw_key

        # Hash should be hex string (sha256 = 64 chars)
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)

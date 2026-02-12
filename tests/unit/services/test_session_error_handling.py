"""Unit tests for session service error handling fixes.

Tests for Phase 2 critical error handling fixes:
- Task #3: Redis failure masking
- Task #4: Database error returning None
- Task #5: Cache parsing without context
- Task #6: UUID parsing exception specificity
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.exc import OperationalError

from apps.api.services.session import SessionService
from apps.api.exceptions.base import APIError


# ===== Task #3: Redis Failure Masking Tests =====


@pytest.fixture
def mock_cache_connection_error():
    """Mock cache that raises ConnectionError."""
    cache = AsyncMock()
    cache.set_json = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    return cache


@pytest.fixture
def mock_cache_timeout_error():
    """Mock cache that raises TimeoutError."""
    cache = AsyncMock()
    cache.set_json = AsyncMock(side_effect=TimeoutError("Redis timeout"))
    return cache


@pytest.fixture
def mock_cache_value_error():
    """Mock cache that raises ValueError (serialization error)."""
    cache = AsyncMock()
    cache.set_json = AsyncMock(side_effect=ValueError("Serialization error"))
    return cache


@pytest.fixture
def mock_db_repo():
    """Mock database repository."""
    repo = AsyncMock()
    repo.create = AsyncMock()
    return repo


@pytest.mark.anyio
async def test_redis_connection_error_raises_api_error_when_cache_configured(
    mock_cache_connection_error, mock_db_repo
):
    """Redis connection errors should raise APIError when cache is configured."""
    service = SessionService(cache=mock_cache_connection_error, db_repo=mock_db_repo)

    with pytest.raises(APIError) as exc_info:
        await service.create_session(model="sonnet")

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "CACHE_UNAVAILABLE"
    assert "Redis" in exc_info.value.message


@pytest.mark.anyio
async def test_redis_timeout_error_raises_api_error_when_cache_configured(
    mock_cache_timeout_error, mock_db_repo
):
    """Redis timeout errors should raise APIError when cache is configured."""
    service = SessionService(cache=mock_cache_timeout_error, db_repo=mock_db_repo)

    with pytest.raises(APIError) as exc_info:
        await service.create_session(model="sonnet")

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "CACHE_UNAVAILABLE"


@pytest.mark.anyio
async def test_other_cache_errors_logged_but_non_fatal(
    mock_cache_value_error, mock_db_repo
):
    """Non-connection cache errors (e.g., serialization) should be non-fatal."""
    service = SessionService(cache=mock_cache_value_error, db_repo=mock_db_repo)

    # Should not raise, just log warning
    session = await service.create_session(model="sonnet")

    assert session is not None
    assert session.model == "sonnet"


# ===== Task #4: Database Error Returning None Tests =====


@pytest.fixture
def mock_cache_miss():
    """Mock cache that returns None (cache miss)."""
    cache = AsyncMock()
    cache.get_json = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def mock_db_repo_operational_error():
    """Mock database repository that raises OperationalError."""
    repo = AsyncMock()
    repo.get = AsyncMock(side_effect=OperationalError("statement", {}, None))
    return repo


@pytest.fixture
def mock_db_repo_generic_error():
    """Mock database repository that raises generic Exception."""
    repo = AsyncMock()
    repo.get = AsyncMock(side_effect=Exception("Unexpected error"))
    return repo


@pytest.mark.anyio
async def test_operational_error_raises_503(
    mock_cache_miss, mock_db_repo_operational_error
):
    """Database operational errors should raise 503 (not return None)."""
    service = SessionService(
        cache=mock_cache_miss, db_repo=mock_db_repo_operational_error
    )

    # Use a valid UUID format
    test_session_id = "12345678-1234-5678-1234-567812345678"

    with pytest.raises(APIError) as exc_info:
        await service.get_session(test_session_id)

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "DATABASE_UNAVAILABLE"


@pytest.mark.anyio
async def test_generic_error_raises_500(mock_cache_miss, mock_db_repo_generic_error):
    """Generic database errors should raise 500 (not return None)."""
    service = SessionService(cache=mock_cache_miss, db_repo=mock_db_repo_generic_error)

    # Use a valid UUID format
    test_session_id = "12345678-1234-5678-1234-567812345678"

    with pytest.raises(APIError) as exc_info:
        await service.get_session(test_session_id)

    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "INTERNAL_ERROR"


# ===== Task #5: Cache Parsing Without Context Tests =====


@pytest.fixture
def mock_cache_corrupted():
    """Mock cache that returns corrupted data."""
    cache = AsyncMock()
    # Missing required field 'model'
    cache.get_json = AsyncMock(
        return_value={
            "id": "test-id",
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            # Missing 'model' field
        }
    )
    cache.delete = AsyncMock()
    return cache


@pytest.mark.anyio
async def test_corrupted_cache_entry_deleted_and_logged(mock_cache_corrupted):
    """Corrupted cache entries should be deleted and logged with context."""
    service = SessionService(cache=mock_cache_corrupted, db_repo=None)

    # Should return None (cache parse failed)
    with patch("apps.api.services.session.logger") as mock_logger:
        result = await service._get_cached_session("test-session-id")

    assert result is None

    # Verify error was logged with context
    mock_logger.error.assert_called_once()
    call_kwargs = mock_logger.error.call_args[1]
    assert call_kwargs["error_id"] == "ERR_CACHE_PARSE_FAILED"
    assert "cache_data_sample" in call_kwargs

    # Verify corrupted entry was deleted
    mock_cache_corrupted.delete.assert_called_once()


@pytest.mark.anyio
async def test_cache_parse_error_includes_data_sample(mock_cache_corrupted):
    """Cache parse errors should include data sample for debugging."""
    service = SessionService(cache=mock_cache_corrupted, db_repo=None)

    with patch("apps.api.services.session.logger") as mock_logger:
        await service._get_cached_session("test-session-id")

    # Check that cache_data_sample was logged
    call_kwargs = mock_logger.error.call_args[1]
    assert "cache_data_sample" in call_kwargs
    # Sample should be truncated to 200 chars
    assert len(call_kwargs["cache_data_sample"]) <= 200


@pytest.mark.anyio
async def test_delete_failure_logged_but_non_fatal():
    """Failure to delete corrupted cache entry should be logged but non-fatal."""
    mock_cache = AsyncMock()
    mock_cache.get_json = AsyncMock(
        return_value={"id": "test-id", "status": "active"}  # Corrupted
    )
    mock_cache.delete = AsyncMock(side_effect=Exception("Delete failed"))

    service = SessionService(cache=mock_cache, db_repo=None)

    with patch("apps.api.services.session.logger") as mock_logger:
        result = await service._get_cached_session("test-session-id")

    # Should still return None (not raise)
    assert result is None

    # Verify warning was logged about delete failure
    warning_calls = [
        call
        for call in mock_logger.warning.call_args_list
        if "failed_to_delete_corrupted_cache" in str(call)
    ]
    assert len(warning_calls) > 0


# ===== Task #6: UUID Parsing Exception Specificity Tests =====


@pytest.mark.anyio
async def test_delete_session_with_invalid_uuid_format() -> None:
    """Test ValueError handling for invalid UUID format in delete_session.

    Task #6: Separate ValueError (expected) from TypeError (bug)
    - ValueError → log debug, return result without crashing
    - Invalid UUID strings should be handled gracefully
    """
    mock_cache = AsyncMock()
    mock_cache.get_json = AsyncMock(return_value=None)  # No cached session
    mock_db_repo = AsyncMock()
    mock_db_repo.get = AsyncMock(side_effect=ValueError("Invalid UUID string"))

    service = SessionService(cache=mock_cache, db_repo=mock_db_repo)

    with patch("apps.api.services.session.logger") as mock_logger:
        # Should not raise, just log debug and proceed
        result = await service.delete_session("not-a-valid-uuid")

    # Verify debug log was written (not error)
    mock_logger.debug.assert_called()
    debug_call = mock_logger.debug.call_args[1]
    assert debug_call["session_id"] == "not-a-valid-uuid"
    assert "invalid_uuid_format" in mock_logger.debug.call_args[0]

    # Should not log as error
    mock_logger.error.assert_not_called()


@pytest.mark.anyio
async def test_delete_session_with_wrong_type_raises() -> None:
    """Test TypeError handling for wrong type passed to UUID constructor.

    Task #6: TypeError indicates programming bug → log error and raise
    - TypeError → log error with exc_info=True, raise exception
    - Helps catch bugs where non-string is passed
    """
    mock_cache = AsyncMock()
    mock_cache.get_json = AsyncMock(return_value=None)
    mock_db_repo = AsyncMock()

    service = SessionService(cache=mock_cache, db_repo=mock_db_repo)

    with patch("apps.api.services.session.logger") as mock_logger:
        with pytest.raises(TypeError):
            # Pass wrong type to trigger TypeError in UUID()
            await service.delete_session(12345)  # type: ignore

    # Verify error log with exc_info
    mock_logger.error.assert_called()
    error_call = mock_logger.error.call_args[1]
    assert error_call["error_id"] == "ERR_UUID_TYPE_ERROR"
    assert error_call["exc_info"] is True


@pytest.mark.anyio
async def test_metadata_fetch_with_invalid_uuid_format() -> None:
    """Test ValueError handling in _get_session_metadata_for_update.

    Task #6: Second location of UUID parsing exception handler
    - ValueError → log debug, return empty dict
    - Should not crash on invalid UUID strings
    """
    mock_db_repo = AsyncMock()
    mock_db_repo.get = AsyncMock(side_effect=ValueError("Invalid UUID string"))

    service = SessionService(cache=None, db_repo=mock_db_repo)

    with patch("apps.api.services.session.logger") as mock_logger:
        result = await service._get_session_metadata_for_update("not-a-uuid")

    # Should return empty dict
    assert result == {}

    # Verify debug log
    mock_logger.debug.assert_called()
    debug_call = mock_logger.debug.call_args[1]
    assert "invalid_uuid_format_in_metadata_fetch" in mock_logger.debug.call_args[0]


@pytest.mark.anyio
async def test_metadata_fetch_with_wrong_type_raises() -> None:
    """Test TypeError handling in _get_session_metadata_for_update.

    Task #6: TypeError is programming bug → raise
    """
    mock_db_repo = AsyncMock()

    service = SessionService(cache=None, db_repo=mock_db_repo)

    with patch("apps.api.services.session.logger") as mock_logger:
        with pytest.raises(TypeError):
            await service._get_session_metadata_for_update(12345)  # type: ignore

    # Verify error log
    mock_logger.error.assert_called()
    error_call = mock_logger.error.call_args[1]
    assert error_call["error_id"] == "ERR_UUID_TYPE_ERROR"
    assert error_call["exc_info"] is True

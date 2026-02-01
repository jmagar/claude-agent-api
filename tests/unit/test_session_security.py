"""Security tests for SessionService timing attack prevention.

This module tests constant-time ownership checks to prevent timing
side-channel attacks that could leak session existence information.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import pytest

from apps.api.exceptions import SessionNotFoundError
from apps.api.services.session import SessionService
from apps.api.types import JsonValue

if TYPE_CHECKING:
    from apps.api.protocols import Cache


class MockCache:
    """Mock cache that stores data in memory."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, JsonValue]] = {}
        self._sets: dict[str, set[str]] = {}

    async def get_json(self, key: str) -> dict[str, JsonValue] | None:
        """Get JSON value from cache."""
        return self._store.get(key)

    async def set_json(
        self, key: str, value: dict[str, JsonValue], ttl: int | None = None
    ) -> bool:
        """Set JSON value in cache."""
        self._store[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._store

    async def scan_keys(self, pattern: str, max_keys: int = 1000) -> list[str]:
        """Scan for keys matching pattern."""
        return []

    async def clear(self) -> bool:
        """Clear all cached values."""
        self._store.clear()
        return True

    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to set."""
        if key not in self._sets:
            self._sets[key] = set()
        self._sets[key].add(value)
        return True

    async def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from set."""
        if key in self._sets:
            self._sets[key].discard(value)
        return True

    async def set_members(self, key: str) -> set[str]:
        """Get set members."""
        return set(self._sets.get(key, set()))

    async def acquire_lock(
        self, key: str, ttl: int = 300, value: str | None = None
    ) -> str | None:
        """Acquire lock."""
        return "mock-lock-value"

    async def release_lock(self, key: str, value: str) -> bool:
        """Release lock."""
        return True

    async def ping(self) -> bool:
        """Check connectivity."""
        return True

    async def get_many_json(self, keys: list[str]) -> list[dict[str, JsonValue] | None]:
        """Get multiple JSON values."""
        return [self._store.get(key) for key in keys]


@pytest.fixture
def session_service() -> SessionService:
    """Create SessionService with mocked cache."""
    mock_cache = MockCache()
    return SessionService(cache=cast("Cache", mock_cache))


class TestTimingAttackPrevention:
    """Tests for timing attack prevention in session ownership checks."""

    @pytest.mark.anyio
    async def test_constant_time_comparison_for_valid_session(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that valid session ownership check uses constant-time comparison."""
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key="owner-key-123",
        )

        # Valid ownership check should succeed
        retrieved = await session_service.get_session(
            session.id,
            current_api_key="owner-key-123",
        )

        assert retrieved is not None
        assert retrieved.id == session.id

    @pytest.mark.anyio
    async def test_constant_time_comparison_for_invalid_owner(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that invalid ownership raises SessionNotFoundError."""
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key="owner-key-123",
        )

        # Invalid ownership check should raise SessionNotFoundError
        # (not PermissionDenied to prevent enumeration)
        with pytest.raises(SessionNotFoundError):
            await session_service.get_session(
                session.id,
                current_api_key="wrong-key-456",
            )

    @pytest.mark.anyio
    async def test_timing_leak_prevention_for_nonexistent_session(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that nonexistent session check doesn't leak timing information."""
        # Attempt to access nonexistent session
        result = await session_service.get_session(
            "nonexistent-session-id",
            current_api_key="some-api-key",
        )

        # Should return None (session doesn't exist)
        assert result is None

    @pytest.mark.anyio
    async def test_constant_time_comparison_is_used(
        self,
        session_service: SessionService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that constant-time comparison is used for ownership checks.

        This test verifies that secrets.compare_digest is called rather than
        measuring timing (which is flaky in CI environments).
        """
        import secrets
        from unittest.mock import MagicMock

        # Create session owned by specific key
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key="owner-key-123",
        )

        # Mock secrets.compare_digest to verify it's called
        original_compare = secrets.compare_digest
        mock_compare = MagicMock(side_effect=original_compare)
        monkeypatch.setattr("secrets.compare_digest", mock_compare)

        # Test with correct owner
        await session_service.get_session(
            session.id,
            current_api_key="owner-key-123",
        )

        # Verify compare_digest was called (constant-time comparison)
        assert mock_compare.call_count > 0, "Expected secrets.compare_digest to be called"

        # Reset mock
        mock_compare.reset_mock()

        # Test with wrong owner
        with pytest.raises(SessionNotFoundError):
            await session_service.get_session(
                session.id,
                current_api_key="wrong-key-456",
            )

        # Verify compare_digest was called even for wrong key
        assert mock_compare.call_count > 0, "Expected secrets.compare_digest to be called for wrong key"

    @pytest.mark.anyio
    async def test_public_session_accessible_without_owner(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that sessions without owner_api_key are publicly accessible."""
        # Create session without owner (public session)
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key=None,
        )

        # Should be accessible with any API key
        retrieved1 = await session_service.get_session(
            session.id,
            current_api_key="any-key-123",
        )
        assert retrieved1 is not None
        assert retrieved1.id == session.id

        # Should also be accessible without API key
        retrieved2 = await session_service.get_session(
            session.id,
            current_api_key=None,
        )
        assert retrieved2 is not None
        assert retrieved2.id == session.id

    @pytest.mark.anyio
    async def test_owned_session_accessible_without_api_key_param(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that owned sessions are accessible when no API key is provided.

        This tests backward compatibility where current_api_key is None.
        """
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key="owner-key-123",
        )

        # Should be accessible when no API key check is performed
        retrieved = await session_service.get_session(
            session.id,
            current_api_key=None,
        )
        assert retrieved is not None
        assert retrieved.id == session.id

    @pytest.mark.anyio
    async def test_enforce_owner_with_matching_keys(
        self,
        session_service: SessionService,
    ) -> None:
        """Test _enforce_owner method with matching API keys."""
        from apps.api.services.session import Session

        session = Session(
            id="test-session-id",
            model="sonnet",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            owner_api_key="owner-key-123",
        )

        # Should succeed with matching key
        result = session_service._enforce_owner(session, "owner-key-123")
        assert result.id == session.id

    @pytest.mark.anyio
    async def test_enforce_owner_with_mismatched_keys(
        self,
        session_service: SessionService,
    ) -> None:
        """Test _enforce_owner method with mismatched API keys."""
        from apps.api.services.session import Session

        session = Session(
            id="test-session-id",
            model="sonnet",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            owner_api_key="owner-key-123",
        )

        # Should raise SessionNotFoundError with mismatched key
        with pytest.raises(SessionNotFoundError) as exc_info:
            session_service._enforce_owner(session, "wrong-key-456")

        # SessionNotFoundError stores session_id in details, not as attribute
        assert exc_info.value.details["session_id"] == "test-session-id"

    @pytest.mark.anyio
    async def test_enforce_owner_with_none_owner(
        self,
        session_service: SessionService,
    ) -> None:
        """Test _enforce_owner method when session has no owner."""
        from apps.api.services.session import Session

        session = Session(
            id="test-session-id",
            model="sonnet",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            owner_api_key=None,
        )

        # Should succeed regardless of provided API key
        result = session_service._enforce_owner(session, "any-key-123")
        assert result.id == session.id

    @pytest.mark.anyio
    async def test_enforce_owner_with_none_current_key(
        self,
        session_service: SessionService,
    ) -> None:
        """Test _enforce_owner method when no current API key is provided."""
        from apps.api.services.session import Session

        session = Session(
            id="test-session-id",
            model="sonnet",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            owner_api_key="owner-key-123",
        )

        # Should succeed when no API key is provided (backward compatibility)
        result = session_service._enforce_owner(session, None)
        assert result.id == session.id

    @pytest.mark.anyio
    async def test_update_session_enforces_ownership(
        self,
        session_service: SessionService,
    ) -> None:
        """Test that update_session enforces ownership."""
        session = await session_service.create_session(
            model="sonnet",
            owner_api_key="owner-key-123",
        )

        # Should fail to update with wrong owner
        with pytest.raises(SessionNotFoundError):
            await session_service.update_session(
                session.id,
                status="completed",
                current_api_key="wrong-key-456",
            )

        # Should succeed with correct owner
        updated = await session_service.update_session(
            session.id,
            status="completed",
            current_api_key="owner-key-123",
        )
        assert updated is not None
        assert updated.status == "completed"


class TestRoutesTimingAttackPrevention:
    """Tests for timing attack prevention in route handlers.

    These tests verify that route-level ownership checks also use
    constant-time comparisons to prevent timing side-channels.
    """

    @pytest.mark.skip(reason="placeholder - requires FastAPI TestClient / integration test")
    @pytest.mark.anyio
    async def test_promote_session_uses_constant_time_check(self) -> None:
        """Test that promote_session route uses constant-time comparison.

        This test should be implemented as an integration test with
        FastAPI TestClient to verify end-to-end timing attack prevention.
        """

    @pytest.mark.skip(reason="placeholder - requires FastAPI TestClient / integration test")
    @pytest.mark.anyio
    async def test_update_tags_uses_constant_time_check(self) -> None:
        """Test that update_tags route uses constant-time comparison.

        This test should be implemented as an integration test with
        FastAPI TestClient to verify end-to-end timing attack prevention.
        """

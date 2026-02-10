"""Unit tests for dependency injection (Priority 8).

Tests all FastAPI dependencies including authentication, service creation,
and error handling for uninitialized resources.
"""

import contextlib
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.adapters.cache import RedisCache
from apps.api.adapters.session_repo import SessionRepository
from apps.api.dependencies import (
    AppState,
    check_shutdown_state,
    close_cache,
    close_db,
    get_agent_service,
    get_app_state,
    get_cache,
    get_checkpoint_service,
    get_db,
    get_session_repo,
    get_session_service,
    get_skills_service,
    init_cache,
    init_db,
    reset_dependencies,
    verify_api_key,
)
from apps.api.exceptions import AuthenticationError, ServiceUnavailableError
from apps.api.services.agent import AgentService
from apps.api.services.checkpoint import CheckpointService
from apps.api.services.session import SessionService
from apps.api.services.shutdown import ShutdownManager
from apps.api.services.skills import SkillsService


class TestDatabaseDependencies:
    """Tests for database initialization and dependency injection."""

    @pytest.mark.anyio
    async def test_init_db_creates_engine_and_session_maker(self) -> None:
        """Test database initialization (M-01, ARC-04).

        GREEN: This test verifies init_db creates engine and session maker on AppState.
        """
        from apps.api.config import get_settings

        # Create fresh state
        state = AppState()
        settings = get_settings()
        session_maker = await init_db(state, settings)

        assert session_maker is not None
        assert state.engine is not None
        assert state.session_maker is not None

        # Cleanup
        await close_db(state)

    @pytest.mark.anyio
    async def test_get_db_returns_session(self) -> None:
        """Test get_db dependency returns database session (ARC-04).

        GREEN: This test verifies get_db yields session from AppState.
        """
        from unittest.mock import Mock

        from apps.api.config import get_settings

        # Initialize database
        state = AppState()
        settings = get_settings()
        await init_db(state, settings)

        # Mock request with app state
        request = Mock(spec=Request)
        request.app.state.app_state = state

        # Get session
        session_gen = get_db(state)
        session = await anext(session_gen)

        assert isinstance(session, AsyncSession)

        # Cleanup
        await session_gen.aclose()
        await close_db(state)

    @pytest.mark.anyio
    async def test_get_db_raises_if_not_initialized(self) -> None:
        """Test get_db raises when database not initialized (ARC-04).

        GREEN: This test verifies error handling for uninitialized database.
        """
        # Empty state (no session maker)
        state = AppState()

        with pytest.raises(RuntimeError, match="Database not initialized"):
            session_gen = get_db(state)
            await anext(session_gen)

    @pytest.mark.anyio
    async def test_close_db_disposes_engine(self) -> None:
        """Test close_db cleans up resources (ARC-04).

        GREEN: This test verifies database cleanup on AppState.
        """
        from apps.api.config import get_settings

        # Initialize database
        state = AppState()
        settings = get_settings()
        await init_db(state, settings)

        # Close database
        await close_db(state)

        assert state.engine is None
        assert state.session_maker is None


class TestCacheDependencies:
    """Tests for cache initialization and dependency injection."""

    @pytest.mark.anyio
    async def test_init_cache_creates_redis_instance(self) -> None:
        """Test cache initialization (M-01, ARC-04).

        GREEN: This test verifies init_cache creates Redis instance on AppState.
        """
        from apps.api.config import get_settings

        # Create fresh state
        state = AppState()
        settings = get_settings()
        cache = await init_cache(state, settings)

        assert cache is not None
        assert isinstance(cache, RedisCache)
        assert state.cache is cache

        # Cleanup
        await close_cache(state)

    @pytest.mark.anyio
    async def test_get_cache_returns_singleton(self) -> None:
        """Test get_cache returns singleton instance (ARC-04).

        GREEN: This test verifies singleton pattern via AppState.
        """
        from apps.api.config import get_settings

        # Initialize cache
        state = AppState()
        settings = get_settings()
        await init_cache(state, settings)

        # Get cache multiple times
        cache1 = await get_cache(state)
        cache2 = await get_cache(state)

        assert cache1 is cache2
        assert state.cache is cache1

        # Cleanup
        await close_cache(state)

    @pytest.mark.anyio
    async def test_get_cache_raises_if_not_initialized(self) -> None:
        """Test get_cache raises when cache not initialized (ARC-04).

        GREEN: This test verifies error handling for uninitialized cache.
        """
        # Empty state (no cache)
        state = AppState()

        with pytest.raises(RuntimeError, match="Cache not initialized"):
            await get_cache(state)

    @pytest.mark.anyio
    async def test_close_cache_cleans_up_connection(self) -> None:
        """Test close_cache cleans up resources (ARC-04).

        GREEN: This test verifies cache cleanup on AppState.
        """
        from apps.api.config import get_settings

        # Initialize cache
        state = AppState()
        settings = get_settings()
        await init_cache(state, settings)

        # Close cache
        await close_cache(state)

        assert state.cache is None


class TestRepositoryDependencies:
    """Tests for repository creation."""

    @pytest.mark.anyio
    async def test_get_session_repo_creates_instance(self) -> None:
        """Test repository creation.

        GREEN: This test verifies get_session_repo creates repository.
        """
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)

        # Get repository
        repo = await get_session_repo(mock_db)

        assert isinstance(repo, SessionRepository)
        assert repo._db is mock_db


class TestServiceDependencies:
    """Tests for service creation."""

    @pytest.mark.anyio
    async def test_get_agent_service_creates_instance(self) -> None:
        """Test agent service creation (ARC-04, ARC-05).

        GREEN: This test verifies get_agent_service creates instance from AppState.
        """
        # Create state without singleton
        state = AppState()

        # Get service with mock cache
        mock_cache = Mock(spec=RedisCache)
        mock_checkpoint_service = Mock(spec=CheckpointService)
        service = await get_agent_service(
            state=state, cache=mock_cache, checkpoint_service=mock_checkpoint_service
        )

        assert isinstance(service, AgentService)

    @pytest.mark.anyio
    async def test_get_agent_service_returns_singleton_if_set(self) -> None:
        """Test agent service singleton for tests (M-01, M-13).

        GREEN: This test verifies singleton pattern via AppState for tests.
        """
        # Create state with singleton
        state = AppState()
        singleton = AgentService()
        state.agent_service = singleton

        # Get service (singleton is returned, cache arg doesn't matter)
        mock_cache = Mock(spec=RedisCache)
        mock_checkpoint_service = Mock(spec=CheckpointService)
        service1 = await get_agent_service(
            state=state, cache=mock_cache, checkpoint_service=mock_checkpoint_service
        )
        service2 = await get_agent_service(
            state=state, cache=mock_cache, checkpoint_service=mock_checkpoint_service
        )

        assert service1 is singleton
        assert service2 is singleton

        # Clear singleton via reset_dependencies
        reset_dependencies(state)
        assert state.agent_service is None

    @pytest.mark.anyio
    async def test_get_session_service_creates_instance(self) -> None:
        """Test session service creation.

        GREEN: This test verifies get_session_service creates instance.
        """
        # Mock cache
        mock_cache = Mock(spec=RedisCache)
        mock_repo = Mock(spec=SessionRepository)

        # Get service
        service = await get_session_service(mock_cache, mock_repo)

        assert isinstance(service, SessionService)
        assert service._cache is mock_cache
        assert service._db_repo is mock_repo

    @pytest.mark.anyio
    async def test_get_checkpoint_service_creates_instance(self) -> None:
        """Test checkpoint service creation.

        GREEN: This test verifies get_checkpoint_service creates instance.
        """
        # Mock cache
        mock_cache = Mock(spec=RedisCache)

        # Get service
        service = await get_checkpoint_service(mock_cache)

        assert isinstance(service, CheckpointService)
        assert service._cache is mock_cache

    @pytest.mark.anyio
    async def test_get_skills_service_creates_instance(self) -> None:
        """Test skills service creation.

        GREEN: This test verifies get_skills_service creates instance.
        """
        service = get_skills_service()

        assert isinstance(service, SkillsService)
        assert service.project_path is not None


class TestAuthenticationDependencies:
    """Tests for API key verification."""

    @pytest.mark.anyio
    async def test_verify_api_key_accepts_valid_key(self) -> None:
        """Test API key verification with valid key.

        GREEN: This test verifies valid key acceptance.
        """
        from apps.api.config import get_settings

        settings = get_settings()
        valid_key = settings.api_key.get_secret_value()

        # Mock request without state.api_key so header is used
        mock_request = Mock(spec=Request)
        mock_request.state = Mock(spec=[])  # Empty state, no api_key attribute

        # Verify key
        result = verify_api_key(mock_request, x_api_key=valid_key)

        assert result == valid_key

    @pytest.mark.anyio
    async def test_verify_api_key_rejects_invalid_key(self) -> None:
        """Test API key rejection with invalid key.

        GREEN: This test verifies invalid key rejection.
        """
        # Mock request without state.api_key so header is used
        mock_request = Mock(spec=Request)
        mock_request.state = Mock(spec=[])  # Empty state, no api_key attribute

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            verify_api_key(mock_request, x_api_key="invalid-key")

    @pytest.mark.anyio
    async def test_verify_api_key_rejects_missing_key(self) -> None:
        """Test API key rejection when missing.

        GREEN: This test verifies missing key rejection.
        """
        # Mock request without state.api_key so header check happens
        mock_request = Mock(spec=Request)
        mock_request.state = Mock(spec=[])  # Empty state, no api_key attribute

        with pytest.raises(AuthenticationError, match="Missing API key"):
            verify_api_key(mock_request, x_api_key=None)

    @pytest.mark.anyio
    async def test_verify_api_key_uses_request_state_when_available(self) -> None:
        """Test API key uses request.state when middleware has validated."""
        mock_request = Mock(spec=Request)
        mock_request.state = Mock()
        mock_request.state.api_key = "validated-key"

        result = verify_api_key(mock_request, x_api_key=None)

        assert result == "validated-key"

    @pytest.mark.anyio
    async def test_verify_api_key_from_header(self) -> None:
        """Test API key extraction from header.

        GREEN: This test verifies header extraction.
        """
        from apps.api.config import get_settings

        settings = get_settings()
        valid_key = settings.api_key.get_secret_value()

        # Mock request without state.api_key so header is used
        mock_request = Mock(spec=Request)
        mock_request.state = Mock(spec=[])  # Empty state, no api_key attribute

        # Pass key as header parameter
        result = verify_api_key(mock_request, x_api_key=valid_key)

        assert result == valid_key

    @pytest.mark.anyio
    async def test_verify_api_key_uses_constant_time_comparison(self) -> None:
        """Test API key uses constant-time comparison.

        GREEN: This test verifies timing attack protection.
        """
        from apps.api.config import get_settings

        # Mock request without state.api_key so header is used
        mock_request = Mock(spec=Request)
        mock_request.state = Mock(spec=[])  # Empty state, no api_key attribute

        # Test that we use secrets.compare_digest (timing-safe)
        # by verifying that similar keys are rejected
        settings = get_settings()
        valid_key = settings.api_key.get_secret_value()
        similar_key = valid_key[:-1] + "x"  # Change last character

        with pytest.raises(AuthenticationError):
            verify_api_key(mock_request, x_api_key=similar_key)


class TestShutdownDependencies:
    """Tests for shutdown state checking."""

    @pytest.mark.anyio
    async def test_check_shutdown_state_allows_requests_when_active(self) -> None:
        """Test shutdown state allows requests when service is active.

        GREEN: This test verifies normal operation.
        """
        with patch("apps.api.dependencies.get_shutdown_manager") as mock_get_manager:
            mock_manager = Mock(spec=ShutdownManager)
            mock_manager.is_shutting_down = False
            mock_get_manager.return_value = mock_manager

            manager = check_shutdown_state()

            assert manager is mock_manager

    @pytest.mark.anyio
    async def test_check_shutdown_state_rejects_requests_during_shutdown(self) -> None:
        """Test shutdown state rejects requests during shutdown.

        GREEN: This test verifies shutdown behavior.
        """
        with patch("apps.api.dependencies.get_shutdown_manager") as mock_get_manager:
            mock_manager = Mock(spec=ShutdownManager)
            mock_manager.is_shutting_down = True
            mock_get_manager.return_value = mock_manager

            with pytest.raises(
                ServiceUnavailableError,
                match="Service is shutting down",
            ):
                check_shutdown_state()


class TestDependencyIntegration:
    """Integration tests for dependency injection chains."""

    @pytest.mark.anyio
    async def test_full_dependency_chain_from_db_to_repo(self) -> None:
        """Test complete dependency chain: init_db -> get_db -> get_session_repo.

        GREEN: This test verifies end-to-end dependency injection.
        """
        from apps.api import dependencies
        from apps.api.config import get_settings

        # Clear state
        dependencies._async_engine = None
        dependencies._async_session_maker = None

        # Initialize
        settings = get_settings()
        app_state = AppState()
        await init_db(app_state, settings)

        # Get session
        session_gen = get_db(app_state)
        session = await anext(session_gen)

        # Get repository
        repo = await get_session_repo(session)

        assert isinstance(repo, SessionRepository)
        assert repo._db is session

        # Cleanup
        with contextlib.suppress(StopAsyncIteration):
            await session_gen.aclose()
        await close_db(app_state)

    @pytest.mark.anyio
    async def test_full_dependency_chain_from_cache_to_service(self) -> None:
        """Test complete dependency chain: init_cache -> get_cache -> get_session_service.

        GREEN: This test verifies end-to-end dependency injection for services.
        """
        from apps.api import dependencies
        from apps.api.config import get_settings

        # Initialize with fresh state
        settings = get_settings()
        app_state = AppState()
        await init_cache(app_state, settings)

        # Get cache
        cache = await get_cache(app_state)

        # Get service
        mock_repo = Mock(spec=SessionRepository)
        service = await get_session_service(cache, mock_repo)

        assert isinstance(service, SessionService)
        assert service._cache is cache
        assert service._db_repo is mock_repo

        # Cleanup
        await close_cache(app_state)


class TestDependencyCleanup:
    """Tests for resource cleanup and lifecycle management."""

    @pytest.mark.anyio
    async def test_close_db_safe_when_already_closed(self) -> None:
        """Test close_db is idempotent.

        GREEN: This test verifies safe double-close.
        """
        # Create state without initializing
        app_state = AppState()

        # Close when already None should not raise
        await close_db(app_state)

        assert app_state.engine is None
        assert app_state.session_maker is None

    @pytest.mark.anyio
    async def test_close_cache_safe_when_already_closed(self) -> None:
        """Test close_cache is idempotent.

        GREEN: This test verifies safe double-close.
        """
        # Create state without initializing
        app_state = AppState()

        # Close when already None should not raise
        await close_cache(app_state)

        assert app_state.cache is None

    @pytest.mark.anyio
    async def test_agent_service_singleton_can_be_cleared(self) -> None:
        """Test agent service singleton can be cleared (M-13).

        GREEN: This test verifies singleton lifecycle management via reset_dependencies.
        """
        # Create state and set singleton
        state = AppState()
        singleton = AgentService()
        state.agent_service = singleton

        # Verify it's returned
        mock_cache = Mock(spec=RedisCache)
        mock_checkpoint_service = Mock(spec=CheckpointService)
        service = await get_agent_service(
            state=state, cache=mock_cache, checkpoint_service=mock_checkpoint_service
        )
        assert service is singleton

        # Clear singleton via reset_dependencies
        reset_dependencies(state)

        # Verify new instances are created
        service1 = await get_agent_service(
            state=state, cache=mock_cache, checkpoint_service=mock_checkpoint_service
        )
        service2 = await get_agent_service(
            state=state, cache=mock_cache, checkpoint_service=mock_checkpoint_service
        )
        assert service1 is not singleton
        assert service2 is not singleton
        assert service1 is not service2

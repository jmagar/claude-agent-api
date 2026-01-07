"""FastAPI dependencies for dependency injection."""

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apps.api.adapters.cache import RedisCache
from apps.api.adapters.session_repo import SessionRepository
from apps.api.config import Settings, get_settings
from apps.api.exceptions import AuthenticationError, ServiceUnavailableError
from apps.api.services.agent import AgentService
from apps.api.services.checkpoint import CheckpointService
from apps.api.services.session import SessionService
from apps.api.services.shutdown import ShutdownManager, get_shutdown_manager

# Global instances (initialized in lifespan)
_async_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None
_redis_cache: RedisCache | None = None


async def init_db(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Initialize database engine and session maker.

    Args:
        settings: Application settings.

    Returns:
        Async session maker.
    """
    global _async_engine, _async_session_maker

    _async_engine = create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.debug,
    )
    _async_session_maker = async_sessionmaker(
        bind=_async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _async_session_maker


async def close_db() -> None:
    """Close database connections."""
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None


async def init_cache(settings: Settings) -> RedisCache:
    """Initialize Redis cache.

    Args:
        settings: Application settings.

    Returns:
        Redis cache instance.
    """
    global _redis_cache
    _redis_cache = await RedisCache.create(settings.redis_url)
    return _redis_cache


async def close_cache() -> None:
    """Close cache connections."""
    global _redis_cache
    if _redis_cache:
        await _redis_cache.close()
        _redis_cache = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        Async database session.

    Raises:
        RuntimeError: If database not initialized.
    """
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized")

    async with _async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_cache() -> RedisCache:
    """Get Redis cache instance.

    Returns:
        Redis cache instance.

    Raises:
        RuntimeError: If cache not initialized.
    """
    if _redis_cache is None:
        raise RuntimeError("Cache not initialized")
    return _redis_cache


async def get_session_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionRepository:
    """Get session repository.

    Args:
        db: Database session.

    Returns:
        Session repository instance.
    """
    return SessionRepository(db)


def verify_api_key(
    _request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
) -> str:
    """Verify API key from header.

    Args:
        request: FastAPI request.
        x_api_key: API key from header.

    Returns:
        Verified API key.

    Raises:
        AuthenticationError: If API key is invalid.
    """
    settings = get_settings()

    if not x_api_key:
        raise AuthenticationError("Missing API key")

    if x_api_key != settings.api_key.get_secret_value():
        raise AuthenticationError("Invalid API key")

    return x_api_key


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    """Get or create agent service singleton.

    Uses lru_cache to ensure single instance across application lifetime.

    Returns:
        AgentService singleton instance.
    """
    return AgentService()


async def get_session_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> SessionService:
    """Get session service instance with injected cache.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        SessionService instance.
    """
    return SessionService(cache=cache)


async def get_checkpoint_service(
    cache: Annotated[RedisCache, Depends(get_cache)],
) -> CheckpointService:
    """Get checkpoint service instance with injected cache.

    Args:
        cache: Redis cache from dependency injection.

    Returns:
        CheckpointService instance.
    """
    return CheckpointService(cache=cache)


def check_shutdown_state() -> ShutdownManager:
    """Check if service is accepting new requests (T131).

    Returns:
        ShutdownManager instance.

    Raises:
        ServiceUnavailableError: If shutdown is in progress.
    """
    manager = get_shutdown_manager()
    if manager.is_shutting_down:
        raise ServiceUnavailableError(
            message="Service is shutting down, not accepting new requests",
            retry_after=30,
        )
    return manager


# Type aliases for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
Cache = Annotated[RedisCache, Depends(get_cache)]
SessionRepo = Annotated[SessionRepository, Depends(get_session_repo)]
ApiKey = Annotated[str, Depends(verify_api_key)]
AgentSvc = Annotated[AgentService, Depends(get_agent_service)]
SessionSvc = Annotated[SessionService, Depends(get_session_service)]
CheckpointSvc = Annotated[CheckpointService, Depends(get_checkpoint_service)]
ShutdownState = Annotated[ShutdownManager, Depends(check_shutdown_state)]

# Best Practices & Code Patterns - Reference Guide

**Date:** 2026-01-29
**Purpose:** Standards for maintaining CLAUDE.md compliance
**Target Audience:** All developers

---

## Table of Contents

1. [Type Safety Patterns](#1-type-safety-patterns)
2. [Async/Await Patterns](#2-asyncawait-patterns)
3. [Dependency Injection](#3-dependency-injection)
4. [Error Handling](#4-error-handling)
5. [API Response Patterns](#5-api-response-patterns)
6. [Database Patterns](#6-database-patterns)
7. [Testing Patterns](#7-testing-patterns)
8. [Function Design](#8-function-design)
9. [Security Patterns](#9-security-patterns)

---

## 1. Type Safety Patterns

### ✅ Correct: Specific Types (Not Any)

```python
from typing import TypedDict, Literal

# Use TypedDict for structured data
class UserResponse(TypedDict):
    id: str
    name: str
    email: str
    role: Literal["admin", "user", "guest"]

def get_user(user_id: str) -> UserResponse:
    """Get user by ID."""
    return {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user",
    }
```

### ❌ Incorrect: Using Any

```python
# DON'T DO THIS
def get_user(user_id: str) -> Any:  # ❌ Too vague
    return {...}

def process_data(data: dict[str, Any]) -> Any:  # ❌ Loses type info
    return data
```

### ✅ Correct: Union Types

```python
# Use Union for multiple possibilities
from typing import Union

def get_config(key: str) -> str | int | bool:
    """Get config value by key."""
    config = {
        "timeout": 30,
        "debug": False,
        "app_name": "api",
    }
    return config.get(key)
```

### ✅ Correct: Protocol for Abstraction

```python
from typing import Protocol

class Cache(Protocol):
    """Cache interface (abstract)."""

    async def get(self, key: str) -> str | None:
        """Get value from cache."""
        ...

    async def set(self, key: str, value: str, ttl: int) -> None:
        """Set value in cache."""
        ...

# Implementation
class RedisCache:
    """Redis implementation of Cache protocol."""

    async def get(self, key: str) -> str | None:
        # Implementation
        return await redis.get(key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        # Implementation
        await redis.setex(key, ttl, value)
```

### ✅ Correct: Generics for Reusable Types

```python
from typing import Generic, TypeVar

T = TypeVar("T")

class Repository(Generic[T], Protocol):
    """Generic repository pattern."""

    async def get(self, id: str) -> T | None:
        """Get item by ID."""
        ...

    async def create(self, item: T) -> T:
        """Create new item."""
        ...

# Usage
class UserRepository(Repository[User]):
    async def get(self, id: str) -> User | None:
        return await db.query(User).filter(User.id == id).first()
```

### ✅ Correct: TypeVar for Validation

```python
from typing import TypeVar, Callable

T = TypeVar("T")

async def validate_and_process(
    value: str,
    validator: Callable[[str], T],
) -> T:
    """Validate value and return typed result."""
    return validator(value)

# Usage
result = await validate_and_process("123", int)  # type: int
```

---

## 2. Async/Await Patterns

### ✅ Correct: Async All I/O

```python
import asyncio
from httpx import AsyncClient

# Async database operations
async def get_user(db: AsyncSession, user_id: str) -> User:
    """Get user from database."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Async HTTP operations
async def fetch_from_api(url: str) -> dict:
    """Fetch from external API."""
    async with AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Async concurrency
async def process_multiple_users(user_ids: list[str]) -> list[User]:
    """Process multiple users concurrently."""
    tasks = [get_user(db, uid) for uid in user_ids]
    return await asyncio.gather(*tasks)
```

### ❌ Incorrect: Blocking I/O

```python
# DON'T DO THIS
import requests
import time

def get_user(db, user_id):  # ❌ Not async
    user = db.query(User).filter(...).first()  # Blocking!
    return user

async def slow_operation():
    time.sleep(1)  # ❌ Blocks event loop!
    response = requests.get("https://api.com")  # ❌ Blocking HTTP
```

### ✅ Correct: Async Context Managers

```python
# Database session
async with AsyncSession(engine) as session:
    user = await get_user(session, "123")

# Cache connection
async with Redis.from_url("redis://localhost") as redis:
    await redis.set("key", "value")
    value = await redis.get("key")

# Custom async context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(db: AsyncSession):
    """Transaction context manager."""
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()

# Usage
async with transaction(db) as session:
    await session.add(user)
```

### ✅ Correct: Async Iteration

```python
# Async generator
async def fetch_all_users(db: AsyncSession) -> AsyncIterator[User]:
    """Fetch users from database lazily."""
    stmt = select(User)
    async for user in await db.stream(stmt):
        yield user

# Usage
async for user in fetch_all_users(db):
    process(user)
```

### ✅ Correct: Async Sleep (Not time.sleep)

```python
import asyncio

# Correct: Use asyncio.sleep()
async def retry_with_backoff(max_retries: int = 3) -> None:
    """Retry with exponential backoff."""
    for attempt in range(max_retries):
        try:
            await some_async_operation()
            return
        except Exception:
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)  # ✅ Doesn't block loop

# Incorrect: DON'T USE time.sleep()
# time.sleep(1)  # ❌ Blocks entire event loop
```

---

## 3. Dependency Injection

### ✅ Correct: Protocol-Based DI

```python
from fastapi import Depends, FastAPI
from typing import Protocol

# Define protocol (interface)
class SessionService(Protocol):
    """Session management interface."""

    async def get_session(self, session_id: str) -> Session:
        """Get session by ID."""
        ...

    async def create_session(self, model: str) -> Session:
        """Create new session."""
        ...

# Implementation
class SessionServiceImpl:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_session(self, session_id: str) -> Session:
        stmt = select(Session).where(Session.id == session_id)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def create_session(self, model: str) -> Session:
        session = Session(id=str(uuid4()), model=model)
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

# Dependency provider
async def get_session_service(
    db: AsyncSession = Depends(get_db),
) -> SessionService:
    """Provide SessionService."""
    return SessionServiceImpl(db)

# Route using DI
@app.post("/sessions")
async def create_session(
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """Create new session."""
    session = await service.create_session(model="sonnet")
    return SessionResponse.from_model(session)
```

### ❌ Incorrect: Global Singletons

```python
# DON'T DO THIS
_session_service = None

def get_session_service():
    global _session_service
    if _session_service is None:
        _session_service = SessionServiceImpl()
    return _session_service

# Hard to test, hard to manage lifecycle
```

### ✅ Correct: Constructor Injection

```python
class QueryHandler:
    """Query handler with injected dependencies."""

    def __init__(
        self,
        agent_service: "AgentService",
        cache: "Cache",
        webhook_service: "WebhookService",
    ) -> None:
        """Initialize with dependencies.

        Args:
            agent_service: Agent execution service.
            cache: Cache implementation.
            webhook_service: Webhook execution service.
        """
        self._agent_service = agent_service
        self._cache = cache
        self._webhook_service = webhook_service

    async def handle(self, query: QueryRequest) -> QueryResponse:
        """Handle query with injected services."""
        # Use injected dependencies
        cached = await self._cache.get(query.id)
        if cached:
            return cached

        response = await self._agent_service.query(query)
        await self._cache.set(query.id, response)
        await self._webhook_service.notify(response)
        return response
```

---

## 4. Error Handling

### ✅ Correct: Specific Exceptions

```python
from fastapi import HTTPException

# Define specific exceptions
class SessionNotFoundError(APIError):
    """Raised when session cannot be found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            message=f"Session {session_id} not found",
            code="SESSION_NOT_FOUND",
            status_code=404,
            details={"session_id": session_id},
        )

# Use specific exceptions
async def get_session(session_id: str) -> Session:
    """Get session by ID."""
    session = await db.query(Session).filter(...).first()
    if not session:
        raise SessionNotFoundError(session_id)  # ✅ Specific
    return session

# Exception handler
@app.exception_handler(SessionNotFoundError)
async def handle_session_not_found(
    request: Request,
    exc: SessionNotFoundError,
) -> JSONResponse:
    """Handle missing session."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
```

### ❌ Incorrect: Generic Exceptions

```python
# DON'T DO THIS
raise Exception("Session not found")  # Too generic
raise ValueError("Bad request")  # Not specific enough
raise RuntimeError("Something went wrong")  # Loses context
```

### ✅ Correct: Context in Exceptions

```python
class QueryError(APIError):
    """Raised when query execution fails."""

    def __init__(
        self,
        message: str,
        code: str,
        query_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=500,
            details={
                "query_id": query_id,
                "session_id": session_id,
            },
        )

# Usage with context
try:
    response = await agent.query(request)
except AgentError as e:
    raise QueryError(
        message=str(e),
        code="AGENT_ERROR",
        query_id=request.id,
        session_id=request.session_id,
    ) from e
```

### ✅ Correct: Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

async def process_query(request: QueryRequest) -> QueryResponse:
    """Process user query."""
    logger.info(
        "processing_query",
        query_id=request.id,
        session_id=request.session_id,
        prompt_length=len(request.prompt),
    )

    try:
        response = await agent.query(request)
        logger.info(
            "query_completed",
            query_id=request.id,
            output_tokens=response.output_tokens,
        )
        return response
    except Exception as e:
        logger.error(
            "query_failed",
            query_id=request.id,
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise
```

---

## 5. API Response Patterns

### ✅ Correct: Pydantic Response Models

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SessionResponse(BaseModel):
    """Session response model."""

    id: str = Field(..., description="Session ID")
    model: str = Field(..., description="Claude model")
    status: Literal["active", "completed", "error"] = Field(...)
    created_at: datetime
    updated_at: datetime
    total_turns: int = Field(default=0, ge=0)
    total_cost_usd: float | None = Field(default=None, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "session-123",
                "model": "sonnet",
                "status": "active",
                "created_at": "2026-01-29T10:00:00Z",
                "updated_at": "2026-01-29T10:05:00Z",
                "total_turns": 3,
                "total_cost_usd": 0.05,
            }
        }

# Route using response model
@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get session details."""
    session = await service.get_session(session_id)
    return SessionResponse(**session.dict())
```

### ✅ Correct: List Response with Pagination

```python
class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool = Field(default=False)

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total + self.page_size - 1) // self.page_size

# Usage
class SessionListResponse(PaginatedResponse[SessionResponse]):
    """Sessions list response."""
    pass

@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
) -> SessionListResponse:
    """List sessions with pagination."""
    result = await service.list_sessions(page, page_size)
    return SessionListResponse(
        items=[SessionResponse(**s.dict()) for s in result.sessions],
        total=result.total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < result.total,
    )
```

### ✅ Correct: SSE Streaming Response

```python
from sse_starlette.sse import EventSourceResponse

@app.post("/query/stream")
async def query_stream(request: QueryRequest) -> EventSourceResponse:
    """Stream query response via SSE."""
    async def event_generator():
        try:
            async for event in agent.query_stream(request):
                yield {
                    "event": event.type,  # "partial", "result", etc.
                    "data": event.model_dump_json(),
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())
```

---

## 6. Database Patterns

### ✅ Correct: Async SQLAlchemy

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Async session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSession(engine) as session:
        try:
            yield session
        finally:
            await session.close()

# Query pattern
async def get_user(db: AsyncSession, user_id: str) -> User | None:
    """Get user by ID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Create pattern
async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create new user."""
    user = User(**user_data.dict())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# Update pattern
async def update_user(
    db: AsyncSession,
    user_id: str,
    user_data: UserUpdate,
) -> User:
    """Update user."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one()

    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user
```

### ✅ Correct: Eager Loading (Prevent N+1)

```python
from sqlalchemy.orm import selectinload

async def get_session_with_messages(
    db: AsyncSession,
    session_id: str,
) -> Session:
    """Get session with all messages loaded."""
    stmt = (
        select(Session)
        .where(Session.id == session_id)
        .options(selectinload(Session.messages))
    )
    result = await db.execute(stmt)
    return result.scalar_one()

# In model definition
class Session(Base):
    """Session model with relationships."""

    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    messages: Mapped[list[SessionMessage]] = relationship(
        lazy="selectin",  # Eager load messages
    )
```

### ✅ Correct: Repository Pattern

```python
class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository."""
        self._db = db

    async def get(self, user_id: str) -> User | None:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """Create new user."""
        user = User(**user_data.dict())
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def list(self, limit: int = 50, offset: int = 0) -> list[User]:
        """List users with pagination."""
        stmt = select(User).limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return result.scalars().all()
```

---

## 7. Testing Patterns

### ✅ Correct: Test Structure

```python
import pytest
from httpx import AsyncClient

# Unit test
@pytest.mark.unit
async def test_validate_email_valid():
    """Test email validation with valid email."""
    assert validate_email("user@example.com") is True

@pytest.mark.unit
async def test_validate_email_invalid():
    """Test email validation with invalid email."""
    assert validate_email("invalid-email") is False

# Integration test
@pytest.mark.integration
async def test_create_user_integration(async_client: AsyncClient):
    """Test user creation end-to-end."""
    response = await async_client.post(
        "/users",
        json={"name": "John", "email": "john@example.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@example.com"

# E2E test (marked to skip in CI)
@pytest.mark.e2e
async def test_full_query_workflow(async_client: AsyncClient):
    """Test complete query workflow."""
    # Create session
    session = await async_client.post("/sessions", json={"model": "sonnet"})
    session_id = session.json()["id"]

    # Submit query
    query = await async_client.post(
        f"/sessions/{session_id}/query",
        json={"prompt": "Hello"},
    )
    assert query.status_code == 200
```

### ✅ Correct: Async Test Fixtures

```python
@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Provide test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
async def cache_service() -> AsyncGenerator[Cache, None]:
    """Provide mock cache service."""
    cache = MockCache()
    yield cache
    await cache.clear()

@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### ✅ Correct: Mocking External Services

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_agent_service() -> AsyncMock:
    """Mock agent service."""
    mock = AsyncMock()
    mock.query.return_value = QueryResponse(
        id="test-123",
        content="test response",
    )
    return mock

@pytest.mark.unit
async def test_query_handler(mock_agent_service: AsyncMock):
    """Test query handler with mocked service."""
    handler = QueryHandler(agent_service=mock_agent_service)
    response = await handler.handle(QueryRequest(prompt="test"))

    assert response.id == "test-123"
    mock_agent_service.query.assert_called_once()
```

---

## 8. Function Design

### ✅ Correct: Function Size (≤50 lines)

```python
# Good: Small, focused function
async def get_user(db: AsyncSession, user_id: str) -> User:
    """Get user by ID.

    Args:
        db: Database session.
        user_id: User identifier.

    Returns:
        User object.

    Raises:
        UserNotFoundError: If user not found.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UserNotFoundError(user_id)

    return user
```

### ❌ Incorrect: Over-Sized Function (100+ lines)

```python
# Bad: Too many responsibilities
async def handle_query(request, db, cache, agent, webhook):  # ❌ Too long
    # Validate request (10 lines)
    # Check cache (15 lines)
    # Execute query (30 lines)
    # Store result (10 lines)
    # Call webhook (10 lines)
    # Handle errors (20 lines)
    # Cleanup (5 lines)
    pass  # Total: 100+ lines
```

### ✅ Correct: Extract Helper Functions

```python
# Better: Separate concerns into small functions

async def _validate_request(request: QueryRequest) -> None:
    """Validate query request."""
    if not request.prompt:
        raise ValueError("Prompt is required")
    if len(request.prompt) > MAX_PROMPT_LENGTH:
        raise ValueError(f"Prompt exceeds {MAX_PROMPT_LENGTH} chars")

async def _check_cache(cache: Cache, query_id: str) -> QueryResponse | None:
    """Check if query result is cached."""
    cached_key = f"query:{query_id}"
    return await cache.get(cached_key)

async def _execute_query(
    agent: AgentService,
    request: QueryRequest,
) -> QueryResponse:
    """Execute query with agent."""
    return await agent.query(request)

async def _store_result(
    cache: Cache,
    query_id: str,
    response: QueryResponse,
    ttl: int = 3600,
) -> None:
    """Store query result in cache."""
    cache_key = f"query:{query_id}"
    await cache.set(cache_key, response.model_dump_json(), ttl)

async def handle_query(
    request: QueryRequest,
    db: AsyncSession,
    cache: Cache,
    agent: AgentService,
) -> QueryResponse:
    """Handle user query (orchestrator).

    Validates, caches, executes, and stores query result.
    """
    await _validate_request(request)

    cached = await _check_cache(cache, request.id)
    if cached:
        return cached

    response = await _execute_query(agent, request)
    await _store_result(cache, request.id, response)
    return response
```

### ✅ Correct: Maximum Parameters (≤5)

```python
# Good: Few parameters
async def create_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    """Create new user."""
    pass

# Bad: Too many parameters
async def create_user_with_validation(  # ❌ Too many params
    db,
    user_data,
    email_service,
    webhook_service,
    cache_service,
    logger,
    validator,
) -> User:
    pass

# Better: Use dependency injection or object
class UserService:
    """Encapsulates user-related operations."""

    def __init__(
        self,
        db: AsyncSession,
        email_service: EmailService,
        webhook_service: WebhookService,
    ) -> None:
        self._db = db
        self._email = email_service
        self._webhook = webhook_service

    async def create_user(self, user_data: UserCreate) -> User:
        """Create user with dependencies injected."""
        user = User(**user_data.dict())
        self._db.add(user)
        await self._db.commit()
        await self._email.send_welcome(user)
        await self._webhook.notify_user_created(user)
        return user
```

---

## 9. Security Patterns

### ✅ Correct: API Key Authentication

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_api_key(credentials = Depends(security)) -> str:
    """Extract and validate API key from Authorization header."""
    api_key = credentials.credentials
    if not api_key or len(api_key) < 20:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/query")
async def query(
    request: QueryRequest,
    api_key: str = Depends(get_api_key),
) -> QueryResponse:
    """Submit query (requires API key)."""
    # Only authenticated users reach here
    return await service.query(request)
```

### ✅ Correct: Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/query")
@limiter.limit("10/minute")
async def query(request: QueryRequest) -> QueryResponse:
    """Submit query (rate limited to 10/min)."""
    return await service.query(request)
```

### ✅ Correct: Input Validation

```python
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    """User creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "SecurePassword123!",
            }
        }

@app.post("/users")
async def create_user(user: UserCreate) -> UserResponse:
    """Create user (validated input)."""
    # Input is automatically validated by Pydantic
    return await service.create_user(user)
```

### ✅ Correct: Secure Defaults

```python
class Settings(BaseSettings):
    """Application settings."""

    # Security
    debug: bool = Field(default=False)  # ✅ Default to False
    cors_origins: list[str] = Field(default=[])  # ✅ Default to empty
    require_https: bool = Field(default=True)  # ✅ Default to True
    api_key: SecretStr = Field(...)  # ✅ Use SecretStr

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        """Validate production settings."""
        if not self.debug and not self.require_https:
            raise ValueError("HTTPS required in production")
        if not self.debug and "*" in self.cors_origins:
            raise ValueError("Wildcard CORS not allowed in production")
        return self
```

---

## Summary Checklist

When writing code, verify:

- ✅ **Type Safety:** No `Any` types, use specific types or Protocols
- ✅ **Async:** All I/O is async, use `await`, no `time.sleep()`
- ✅ **Functions:** ≤50 lines, ≤5 parameters, single responsibility
- ✅ **Error Handling:** Specific exceptions, context in messages
- ✅ **Testing:** Unit tests for logic, integration tests for flows
- ✅ **Database:** Async SQLAlchemy, eager loading, pagination
- ✅ **API Responses:** Pydantic models, consistent schema
- ✅ **Docstrings:** Google-style on all public APIs
- ✅ **Security:** Input validation, rate limiting, HTTPS

---

**Generated:** 2026-01-29
**Version:** 1.0
**Maintainer:** Claude Code AI

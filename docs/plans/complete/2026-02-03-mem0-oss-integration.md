# Mem0 OSS Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate Mem0 OSS library to provide persistent, graph-enhanced memory across conversations with multi-tenant isolation.

**Architecture:** Protocol-based dependency injection with Mem0 Memory client wrapped in a MemoryService. Query flow intercepts requests to search/inject memories before SDK execution and extracts/stores memories after responses. Multi-tenant isolation via user_id=api_key scoping.

**Tech Stack:** Python 3.11+, FastAPI, mem0ai, Qdrant, Neo4j, SQLite, Pydantic, structlog

---

## Task 1: Add mem0ai Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add mem0ai to dependencies**

```bash
uv add mem0ai
```

Expected: mem0ai added to pyproject.toml and uv.lock updated

**Step 2: Verify installation**

```bash
uv run python -c "from mem0 import Memory; print('mem0ai installed successfully')"
```

Expected: "mem0ai installed successfully" printed to stdout

**Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add mem0ai dependency"
```

---

## Task 2: Define Memory Protocol Interface

**Files:**
- Create: `apps/api/protocols.py` (modify existing)

**Step 1: Write the failing test**

Create: `tests/unit/test_memory_protocol.py`

```python
"""Tests for memory protocol interface."""
import pytest
from apps.api.protocols import MemoryProtocol


def test_memory_protocol_has_required_methods() -> None:
    """Memory protocol must define search, add, get_all, delete methods."""
    assert hasattr(MemoryProtocol, "search")
    assert hasattr(MemoryProtocol, "add")
    assert hasattr(MemoryProtocol, "get_all")
    assert hasattr(MemoryProtocol, "delete")
    assert hasattr(MemoryProtocol, "delete_all")
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_memory_protocol.py::test_memory_protocol_has_required_methods -v
```

Expected: FAIL with "cannot import name 'MemoryProtocol'"

**Step 3: Write minimal implementation**

Add to: `apps/api/protocols.py`

```python
from typing import Protocol, TypedDict


class MemorySearchResult(TypedDict):
    """Result from memory search."""
    id: str
    memory: str
    score: float
    metadata: dict[str, object]


class MemoryProtocol(Protocol):
    """Protocol for memory operations."""

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        enable_graph: bool = True,
    ) -> list[MemorySearchResult]:
        """Search memories for a user."""
        ...

    async def add(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, object] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, object]]:
        """Add memories from conversation."""
        ...

    async def get_all(
        self,
        user_id: str,
    ) -> list[dict[str, object]]:
        """Get all memories for a user."""
        ...

    async def delete(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory."""
        ...

    async def delete_all(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user."""
        ...
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/test_memory_protocol.py::test_memory_protocol_has_required_methods -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/protocols.py tests/unit/test_memory_protocol.py
git commit -m "feat: add memory protocol interface"
```

---

## Task 3: Add Memory Configuration to Settings

**Files:**
- Modify: `apps/api/config.py`

**Step 1: Write the failing test**

Create: `tests/unit/test_memory_config.py`

```python
"""Tests for memory configuration."""
import os
import pytest
from apps.api.config import Settings


def test_memory_config_loaded_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Memory config should load from environment variables."""
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("NEO4J_URL", "bolt://localhost:54687")
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "testpass")
    monkeypatch.setenv("QDRANT_URL", "http://localhost:53333")
    monkeypatch.setenv("TEI_URL", "http://100.74.16.82:52000")

    settings = Settings()

    assert settings.llm_api_key == "test-key"
    assert settings.neo4j_url == "bolt://localhost:54687"
    assert settings.neo4j_username == "neo4j"
    assert settings.neo4j_password == "testpass"
    assert settings.qdrant_url == "http://localhost:53333"
    assert settings.tei_url == "http://100.74.16.82:52000"


def test_memory_config_defaults() -> None:
    """Memory config should have sensible defaults."""
    settings = Settings()

    assert settings.mem0_collection_name == "mem0_memories"
    assert settings.mem0_embedding_dims == 1024
    assert settings.mem0_agent_id == "main"
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_memory_config.py -v
```

Expected: FAIL with "Settings has no attribute 'llm_api_key'"

**Step 3: Write minimal implementation**

Add to: `apps/api/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Existing settings...

    # Mem0 LLM Configuration
    llm_api_key: str = ""
    llm_base_url: str = "https://cli-api.tootie.tv/v1"
    llm_model: str = "gemini-3-flash-preview"

    # Neo4j Configuration
    neo4j_url: str = "bolt://localhost:54687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "neo4jpassword"
    neo4j_database: str = "neo4j"

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:53333"

    # TEI Configuration
    tei_url: str = "http://100.74.16.82:52000"

    # Mem0 Configuration
    mem0_collection_name: str = "mem0_memories"
    mem0_embedding_dims: int = 1024
    mem0_agent_id: str = "main"
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/test_memory_config.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/config.py tests/unit/test_memory_config.py
git commit -m "feat: add memory configuration to settings"
```

---

## Task 4: Create Mem0 Client Adapter

**Files:**
- Create: `apps/api/adapters/memory.py`

**Step 1: Write the failing test**

Create: `tests/unit/adapters/test_memory_adapter.py`

```python
"""Tests for Mem0 memory adapter."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        llm_api_key="test-key",
        llm_base_url="https://cli-api.tootie.tv/v1",
        llm_model="gemini-3-flash-preview",
        neo4j_url="bolt://localhost:54687",
        neo4j_username="neo4j",
        neo4j_password="testpass",
        neo4j_database="neo4j",
        qdrant_url="http://localhost:53333",
        tei_url="http://100.74.16.82:52000",
        mem0_collection_name="mem0_memories",
        mem0_embedding_dims=1024,
        mem0_agent_id="main",
    )


@pytest.mark.asyncio
async def test_mem0_adapter_search(settings: Settings) -> None:
    """Mem0 adapter should search memories for a user."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.search.return_value = [
            {
                "id": "mem_123",
                "memory": "User prefers technical explanations",
                "score": 0.95,
                "metadata": {"category": "preferences"},
            }
        ]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.search(
            query="What are user preferences?",
            user_id="test-api-key",
            limit=10,
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_123"
        assert results[0]["memory"] == "User prefers technical explanations"
        assert results[0]["score"] == 0.95
        mock_memory.search.assert_called_once_with(
            query="What are user preferences?",
            user_id="test-api-key",
            agent_id="main",
            limit=10,
        )


@pytest.mark.asyncio
async def test_mem0_adapter_add(settings: Settings) -> None:
    """Mem0 adapter should add memories from conversation."""
    with patch("apps.api.adapters.memory.Memory") as mock_memory_class:
        mock_memory = MagicMock()
        mock_memory.add.return_value = [
            {"id": "mem_456", "memory": "User likes Python"}
        ]
        mock_memory_class.from_config.return_value = mock_memory

        adapter = Mem0MemoryAdapter(settings)
        results = await adapter.add(
            messages="I really enjoy coding in Python",
            user_id="test-api-key",
            metadata={"source": "conversation"},
            enable_graph=True,
        )

        assert len(results) == 1
        assert results[0]["id"] == "mem_456"
        mock_memory.add.assert_called_once_with(
            messages="I really enjoy coding in Python",
            user_id="test-api-key",
            agent_id="main",
            metadata={"source": "conversation"},
        )
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/adapters/test_memory_adapter.py -v
```

Expected: FAIL with "cannot import name 'Mem0MemoryAdapter'"

**Step 3: Write minimal implementation**

Create: `apps/api/adapters/memory.py`

```python
"""Mem0 memory adapter implementation."""
import asyncio
from typing import cast
from mem0 import Memory
from apps.api.config import Settings
from apps.api.protocols import MemorySearchResult
import structlog

logger = structlog.get_logger(__name__)


class Mem0MemoryAdapter:
    """Adapter for Mem0 memory operations."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Mem0 client with configuration."""
        self._settings = settings
        self._agent_id = settings.mem0_agent_id

        # Parse Qdrant URL
        qdrant_parts = settings.qdrant_url.replace("http://", "").replace("https://", "").split(":")
        qdrant_host = qdrant_parts[0]
        qdrant_port = int(qdrant_parts[1]) if len(qdrant_parts) > 1 else 6333

        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "base_url": settings.llm_base_url,
                    "model": settings.llm_model,
                    "api_key": settings.llm_api_key,
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "huggingface_base_url": f"{settings.tei_url}/v1",
                    "embedding_dims": settings.mem0_embedding_dims,
                },
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": qdrant_host,
                    "port": qdrant_port,
                    "collection_name": settings.mem0_collection_name,
                    "embedding_model_dims": settings.mem0_embedding_dims,
                    "distance": "cosine",
                    "on_disk": True,
                },
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": settings.neo4j_url,
                    "username": settings.neo4j_username,
                    "password": settings.neo4j_password,
                    "database": settings.neo4j_database,
                },
            },
            "version": "v1.1",
        }

        self._memory = Memory.from_config(config)
        logger.info("mem0_client_initialized", config_version="v1.1")

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        enable_graph: bool = True,
    ) -> list[MemorySearchResult]:
        """Search memories for a user."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._memory.search(
                query=query,
                user_id=user_id,
                agent_id=self._agent_id,
                limit=limit,
                enable_graph=enable_graph,
            ),
        )

        return [
            cast(
                MemorySearchResult,
                {
                    "id": r["id"],
                    "memory": r["memory"],
                    "score": r.get("score", 0.0),
                    "metadata": r.get("metadata", {}),
                },
            )
            for r in results
        ]

    async def add(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, object] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, object]]:
        """Add memories from conversation."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._memory.add(
                messages=messages,
                user_id=user_id,
                agent_id=self._agent_id,
                metadata=metadata or {},
                enable_graph=enable_graph,
            ),
        )
        return results

    async def get_all(
        self,
        user_id: str,
    ) -> list[dict[str, object]]:
        """Get all memories for a user."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self._memory.get_all(
                user_id=user_id,
                agent_id=self._agent_id,
            ),
        )
        return results

    async def delete(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._memory.delete(
                memory_id=memory_id,
                user_id=user_id,
            ),
        )

    async def delete_all(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._memory.delete_all(
                user_id=user_id,
            ),
        )
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/adapters/test_memory_adapter.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/adapters/memory.py tests/unit/adapters/test_memory_adapter.py
git commit -m "feat: add mem0 memory adapter"
```

---

## Task 5: Create Memory Service

**Files:**
- Create: `apps/api/services/memory.py`

**Step 1: Write the failing test**

Create: `tests/unit/services/test_memory_service.py`

```python
"""Tests for memory service."""
import pytest
from unittest.mock import AsyncMock
from apps.api.services.memory import MemoryService
from apps.api.protocols import MemoryProtocol, MemorySearchResult


@pytest.fixture
def mock_memory_client() -> AsyncMock:
    """Create mock memory client."""
    mock = AsyncMock(spec=MemoryProtocol)
    mock.search.return_value = [
        {
            "id": "mem_123",
            "memory": "User prefers technical explanations",
            "score": 0.95,
            "metadata": {"category": "preferences"},
        }
    ]
    mock.add.return_value = [{"id": "mem_456", "memory": "User likes Python"}]
    mock.get_all.return_value = [
        {"id": "mem_123", "memory": "User prefers technical explanations"},
        {"id": "mem_456", "memory": "User likes Python"},
    ]
    return mock


@pytest.mark.asyncio
async def test_memory_service_search(mock_memory_client: AsyncMock) -> None:
    """Memory service should search and return results."""
    service = MemoryService(mock_memory_client)

    results = await service.search_memories(
        query="What are user preferences?",
        user_id="test-api-key",
        limit=10,
    )

    assert len(results) == 1
    assert results[0]["memory"] == "User prefers technical explanations"
    mock_memory_client.search.assert_called_once_with(
        query="What are user preferences?",
        user_id="test-api-key",
        limit=10,
        enable_graph=True,
    )


@pytest.mark.asyncio
async def test_memory_service_add(mock_memory_client: AsyncMock) -> None:
    """Memory service should add memories."""
    service = MemoryService(mock_memory_client)

    results = await service.add_memory(
        messages="I really enjoy coding in Python",
        user_id="test-api-key",
        metadata={"source": "conversation"},
    )

    assert len(results) == 1
    mock_memory_client.add.assert_called_once_with(
        messages="I really enjoy coding in Python",
        user_id="test-api-key",
        metadata={"source": "conversation"},
        enable_graph=True,
    )


@pytest.mark.asyncio
async def test_memory_service_format_context(mock_memory_client: AsyncMock) -> None:
    """Memory service should format memories as context string."""
    service = MemoryService(mock_memory_client)

    context = await service.format_memory_context(
        query="What are user preferences?",
        user_id="test-api-key",
    )

    assert "User prefers technical explanations" in context
    assert "RELEVANT MEMORIES" in context
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/services/test_memory_service.py -v
```

Expected: FAIL with "cannot import name 'MemoryService'"

**Step 3: Write minimal implementation**

Create: `apps/api/services/memory.py`

```python
"""Memory service for managing conversation memories."""
from apps.api.protocols import MemoryProtocol, MemorySearchResult
import structlog

logger = structlog.get_logger(__name__)


class MemoryService:
    """Service for memory operations."""

    def __init__(self, memory_client: MemoryProtocol) -> None:
        """Initialize memory service."""
        self._client = memory_client

    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        enable_graph: bool = True,
    ) -> list[MemorySearchResult]:
        """Search memories for a user."""
        return await self._client.search(
            query=query,
            user_id=user_id,
            limit=limit,
            enable_graph=enable_graph,
        )

    async def add_memory(
        self,
        messages: str,
        user_id: str,
        metadata: dict[str, object] | None = None,
        enable_graph: bool = True,
    ) -> list[dict[str, object]]:
        """Add memories from conversation."""
        return await self._client.add(
            messages=messages,
            user_id=user_id,
            metadata=metadata,
            enable_graph=enable_graph,
        )

    async def get_all_memories(
        self,
        user_id: str,
    ) -> list[dict[str, object]]:
        """Get all memories for a user."""
        return await self._client.get_all(user_id=user_id)

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str,
    ) -> None:
        """Delete a specific memory."""
        await self._client.delete(memory_id=memory_id, user_id=user_id)

    async def delete_all_memories(
        self,
        user_id: str,
    ) -> None:
        """Delete all memories for a user."""
        await self._client.delete_all(user_id=user_id)

    async def format_memory_context(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
    ) -> str:
        """Format memories as context string for injection into prompts."""
        memories = await self.search_memories(
            query=query,
            user_id=user_id,
            limit=limit,
        )

        if not memories:
            return ""

        context_parts = ["RELEVANT MEMORIES:"]
        for mem in memories:
            context_parts.append(f"- {mem['memory']}")

        return "\n".join(context_parts)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/services/test_memory_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/services/memory.py tests/unit/services/test_memory_service.py
git commit -m "feat: add memory service"
```

---

## Task 6: Add Memory Dependency Injection

**Files:**
- Modify: `apps/api/dependencies.py`

**Step 1: Write the failing test**

Create: `tests/unit/test_memory_dependencies.py`

```python
"""Tests for memory dependency injection."""
import pytest
from fastapi import FastAPI
from apps.api.dependencies import get_memory_service
from apps.api.services.memory import MemoryService


def test_get_memory_service_returns_service() -> None:
    """get_memory_service should return MemoryService instance."""
    service = get_memory_service()
    assert isinstance(service, MemoryService)
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_memory_dependencies.py -v
```

Expected: FAIL with "cannot import name 'get_memory_service'"

**Step 3: Write minimal implementation**

Add to: `apps/api/dependencies.py`

```python
from functools import lru_cache
from apps.api.config import Settings
from apps.api.adapters.memory import Mem0MemoryAdapter
from apps.api.services.memory import MemoryService


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache
def get_memory_service() -> MemoryService:
    """Get cached memory service instance.

    Note: The Memory client is initialized once and reused (singleton).
    This is intentional - Mem0 Memory instances are stateless and can be
    safely shared across requests. The lru_cache ensures only one instance
    is created per process.
    """
    settings = get_settings()
    adapter = Mem0MemoryAdapter(settings)
    return MemoryService(adapter)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/test_memory_dependencies.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/dependencies.py tests/unit/test_memory_dependencies.py
git commit -m "feat: add memory service dependency injection"
```

---

## Task 7: Create Memory Management API Schemas

**Files:**
- Create: `apps/api/schemas/memory.py`

**Step 1: Write the failing test**

Create: `tests/unit/schemas/test_memory_schemas.py`

```python
"""Tests for memory schemas."""
import pytest
from pydantic import ValidationError
from apps.api.schemas.memory import (
    MemoryAddRequest,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryListResponse,
)


def test_memory_add_request_valid() -> None:
    """MemoryAddRequest should validate correct data."""
    request = MemoryAddRequest(
        messages="User prefers technical explanations",
        metadata={"category": "preferences"},
        enable_graph=True,
    )
    assert request.messages == "User prefers technical explanations"
    assert request.metadata == {"category": "preferences"}
    assert request.enable_graph is True


def test_memory_add_request_defaults() -> None:
    """MemoryAddRequest should have sensible defaults."""
    request = MemoryAddRequest(messages="Test memory")
    assert request.metadata is None
    assert request.enable_graph is True


def test_memory_search_request_valid() -> None:
    """MemorySearchRequest should validate correct data."""
    request = MemorySearchRequest(
        query="What are user preferences?",
        limit=10,
        enable_graph=True,
    )
    assert request.query == "What are user preferences?"
    assert request.limit == 10
    assert request.enable_graph is True


def test_memory_search_request_defaults() -> None:
    """MemorySearchRequest should have sensible defaults."""
    request = MemorySearchRequest(query="Test query")
    assert request.limit == 10
    assert request.enable_graph is True


def test_memory_search_response_valid() -> None:
    """MemorySearchResponse should validate correct data."""
    response = MemorySearchResponse(
        results=[
            {
                "id": "mem_123",
                "memory": "User prefers technical explanations",
                "score": 0.95,
                "metadata": {"category": "preferences"},
            }
        ],
        count=1,
    )
    assert len(response.results) == 1
    assert response.count == 1
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/schemas/test_memory_schemas.py -v
```

Expected: FAIL with "cannot import name 'MemoryAddRequest'"

**Step 3: Write minimal implementation**

Create: `apps/api/schemas/memory.py`

```python
"""Memory API request/response schemas."""
from pydantic import BaseModel, Field


class MemoryAddRequest(BaseModel):
    """Request to add a memory."""

    messages: str = Field(..., description="Content to extract memories from")
    metadata: dict[str, object] | None = Field(
        None, description="Optional metadata to attach to memories"
    )
    enable_graph: bool = Field(
        True, description="Enable graph memory extraction (slower but richer)"
    )


class MemorySearchRequest(BaseModel):
    """Request to search memories."""

    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    enable_graph: bool = Field(
        True, description="Include graph context in search"
    )


class MemoryResult(BaseModel):
    """Single memory result."""

    id: str
    memory: str
    score: float = 0.0
    metadata: dict[str, object] = Field(default_factory=dict)


class MemorySearchResponse(BaseModel):
    """Response from memory search."""

    results: list[MemoryResult]
    count: int


class MemoryListResponse(BaseModel):
    """Response from listing all memories."""

    memories: list[dict[str, object]]
    count: int


class MemoryDeleteResponse(BaseModel):
    """Response from deleting memory."""

    deleted: bool
    message: str
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/unit/schemas/test_memory_schemas.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/api/schemas/memory.py tests/unit/schemas/test_memory_schemas.py
git commit -m "feat: add memory API schemas"
```

---

## Remaining Tasks (8-14) Continue in Same Pattern...

Due to length constraints, tasks 8-14 follow the same TDD pattern:
- Task 8: Create Memory Management API Routes
- Task 9: Integrate Memory into Query Flow
- Task 10: Add Multi-Tenant Isolation Tests
- Task 11: Add Environment Variables Documentation
- Task 12: Run Full Test Suite
- Task 13: Update API Documentation
- Task 14: Final Verification

Each follows: Write failing test → Run (FAIL) → Implement → Run (PASS) → Commit

---

## Success Criteria Checklist

- [ ] mem0ai dependency added to pyproject.toml
- [ ] Memory protocol interface defined
- [ ] Memory configuration in settings
- [ ] Mem0 client adapter implemented
- [ ] Memory service created
- [ ] Dependency injection configured
- [ ] API schemas defined
- [ ] Memory management routes implemented
- [ ] Memory integrated into query flow
- [ ] Multi-tenant isolation tested
- [ ] Environment variables documented
- [ ] All tests pass (≥90% unit, ≥80% integration)
- [ ] Type checker passes (zero errors)
- [ ] Linter passes (zero errors)
- [ ] API documentation updated
- [ ] Manual verification complete

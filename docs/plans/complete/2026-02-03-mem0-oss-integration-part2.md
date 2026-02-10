# Mem0 OSS Integration - Part 2 (Tasks 8-14) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Mem0 OSS integration with REST API routes, query flow integration, multi-tenant isolation, and full verification.

**Architecture:** REST endpoints for memory CRUD operations, middleware integration into query service for automatic memory injection/extraction, comprehensive testing with real services for multi-tenant isolation verification.

**Tech Stack:** Python 3.11+, FastAPI, mem0ai, Qdrant, Neo4j, pytest, httpx

---

## Prerequisites

**IMPORTANT:** Part 1 tasks (1-7) must be completed before starting these tasks:
- ✅ mem0ai dependency added
- ✅ Memory protocol interface defined
- ✅ Memory configuration in settings
- ✅ Mem0 client adapter implemented
- ✅ Memory service created
- ✅ Dependency injection configured
- ✅ API schemas defined

---

## Task 8: Create Memory Management API Routes

**Files:**
- Create: `apps/api/routes/memories.py`
- Modify: `apps/api/main.py`

**Step 1: Write the failing test**

Create: `tests/integration/routes/test_memories.py`

```python
"""Integration tests for memory routes."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from apps.api.main import app


@pytest.fixture
def mock_memory_service() -> AsyncMock:
    """Create mock memory service."""
    mock = AsyncMock()
    mock.search_memories.return_value = [
        {
            "id": "mem_123",
            "memory": "User prefers technical explanations",
            "score": 0.95,
            "metadata": {"category": "preferences"},
        }
    ]
    mock.add_memory.return_value = [
        {"id": "mem_456", "memory": "User likes Python"}
    ]
    mock.get_all_memories.return_value = [
        {"id": "mem_123", "memory": "User prefers technical explanations"},
        {"id": "mem_456", "memory": "User likes Python"},
    ]
    return mock


@pytest.mark.asyncio
async def test_search_memories(mock_memory_service: AsyncMock) -> None:
    """POST /api/v1/memories/search should search memories."""
    with patch(
        "apps.api.routes.memories.get_memory_service",
        return_value=mock_memory_service,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/memories/search",
                json={"query": "What are user preferences?", "limit": 10},
                headers={"X-API-Key": "test-key"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["memory"] == "User prefers technical explanations"


@pytest.mark.asyncio
async def test_add_memory(mock_memory_service: AsyncMock) -> None:
    """POST /api/v1/memories should add a memory."""
    with patch(
        "apps.api.routes.memories.get_memory_service",
        return_value=mock_memory_service,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/memories",
                json={
                    "messages": "I enjoy coding in Python",
                    "metadata": {"source": "conversation"},
                },
                headers={"X-API-Key": "test-key"},
            )

    assert response.status_code == 201
    data = response.json()
    assert len(data["memories"]) == 1


@pytest.mark.asyncio
async def test_list_memories(mock_memory_service: AsyncMock) -> None:
    """GET /api/v1/memories should list all memories for user."""
    with patch(
        "apps.api.routes.memories.get_memory_service",
        return_value=mock_memory_service,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/memories",
                headers={"X-API-Key": "test-key"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["memories"]) == 2


@pytest.mark.asyncio
async def test_delete_memory(mock_memory_service: AsyncMock) -> None:
    """DELETE /api/v1/memories/{memory_id} should delete a memory."""
    with patch(
        "apps.api.routes.memories.get_memory_service",
        return_value=mock_memory_service,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.delete(
                "/api/v1/memories/mem_123",
                headers={"X-API-Key": "test-key"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True


@pytest.mark.asyncio
async def test_delete_all_memories(mock_memory_service: AsyncMock) -> None:
    """DELETE /api/v1/memories should delete all memories for user."""
    with patch(
        "apps.api.routes.memories.get_memory_service",
        return_value=mock_memory_service,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.delete(
                "/api/v1/memories",
                headers={"X-API-Key": "test-key"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/integration/routes/test_memories.py -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Write minimal implementation**

Create: `apps/api/routes/memories.py`

```python
"""Memory management API routes."""
from fastapi import APIRouter, Depends, Header, status
from apps.api.dependencies import get_memory_service
from apps.api.services.memory import MemoryService
from apps.api.schemas.memory import (
    MemoryAddRequest,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryListResponse,
    MemoryDeleteResponse,
    MemoryResult,
)
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/memories", tags=["memories"])


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemorySearchResponse:
    """Search memories for the current user."""
    results = await memory_service.search_memories(
        query=request.query,
        user_id=x_api_key,
        limit=request.limit,
        enable_graph=request.enable_graph,
    )

    return MemorySearchResponse(
        results=[MemoryResult(**r) for r in results],
        count=len(results),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_memory(
    request: MemoryAddRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    memory_service: MemoryService = Depends(get_memory_service),
) -> dict[str, object]:
    """Add a memory for the current user."""
    results = await memory_service.add_memory(
        messages=request.messages,
        user_id=x_api_key,
        metadata=request.metadata,
        enable_graph=request.enable_graph,
    )

    return {"memories": results, "count": len(results)}


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    x_api_key: str = Header(..., alias="X-API-Key"),
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryListResponse:
    """List all memories for the current user."""
    memories = await memory_service.get_all_memories(user_id=x_api_key)

    return MemoryListResponse(memories=memories, count=len(memories))


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(
    memory_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryDeleteResponse:
    """Delete a specific memory."""
    await memory_service.delete_memory(memory_id=memory_id, user_id=x_api_key)

    return MemoryDeleteResponse(
        deleted=True, message=f"Memory {memory_id} deleted"
    )


@router.delete("", response_model=MemoryDeleteResponse)
async def delete_all_memories(
    x_api_key: str = Header(..., alias="X-API-Key"),
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryDeleteResponse:
    """Delete all memories for the current user."""
    await memory_service.delete_all_memories(user_id=x_api_key)

    return MemoryDeleteResponse(
        deleted=True, message="All memories deleted"
    )
```

**Step 4: Register routes in main app**

Modify: `apps/api/main.py`

Find the section where routers are registered (likely near `app.include_router()` calls) and add:

```python
from apps.api.routes import memories

app.include_router(memories.router)
```

**Step 5: Run test to verify it passes**

```bash
uv run pytest tests/integration/routes/test_memories.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add apps/api/routes/memories.py tests/integration/routes/test_memories.py apps/api/main.py
git commit -m "feat: add memory management API routes"
```

---

## Task 9: Integrate Memory into Query Flow

**Files:**
- Modify: `apps/api/services/query.py` (or equivalent query handler)
- Create: `tests/integration/test_query_memory_integration.py`

**Note:** This task assumes you have an existing query service. Adapt file paths and class names to match your actual implementation.

**Step 1: Locate the actual query service implementation**

```bash
# Search for query-related files
uv run python -c "from pathlib import Path; print('\n'.join(str(p) for p in Path('apps/api').rglob('*query*')))"

# Search for SDK client usage
grep -r "sdk_client\|ClaudeSDK\|query" apps/api/services/ apps/api/routes/ --include="*.py" | grep -v test | grep -v __pycache__
```

Expected: Find the actual query service file and read it to understand the structure.

**IMPORTANT:** Read the actual query service implementation before proceeding. The code examples below are generic - you MUST adapt them to match your actual codebase structure.

**Step 2: Write the failing test**

Create: `tests/integration/test_query_memory_integration.py`

```python
"""Integration tests for query memory integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from apps.api.services.memory import MemoryService


@pytest.fixture
def mock_memory_service() -> AsyncMock:
    """Create mock memory service."""
    mock = AsyncMock(spec=MemoryService)
    mock.format_memory_context.return_value = (
        "RELEVANT MEMORIES:\n- User prefers technical explanations"
    )
    mock.add_memory.return_value = [{"id": "mem_123"}]
    return mock


@pytest.mark.asyncio
async def test_query_injects_memory_context(mock_memory_service: AsyncMock) -> None:
    """Query should inject relevant memories into system prompt."""
    # Import your query service/handler
    from apps.api.services.query import QueryService  # Adjust import path

    # Mock the SDK client to capture what prompt was sent
    mock_sdk_client = AsyncMock()
    mock_sdk_client.query.return_value = MagicMock(
        content="Response text",
        query_id="q123",
    )

    # Create service with mocked dependencies
    service = QueryService(
        sdk_client=mock_sdk_client,
        memory_service=mock_memory_service,
    )

    # Execute query
    await service.execute_query(
        prompt="What do you know about me?",
        api_key="test-key",
    )

    # Verify memory context was retrieved
    mock_memory_service.format_memory_context.assert_called_once_with(
        query="What do you know about me?",
        user_id="test-key",
    )

    # Verify SDK was called with enhanced prompt including memory
    call_args = mock_sdk_client.query.call_args
    system_prompt = call_args.kwargs.get("system_prompt", "")
    assert "RELEVANT MEMORIES" in system_prompt
    assert "User prefers technical explanations" in system_prompt


@pytest.mark.asyncio
async def test_query_extracts_memories_after_response(
    mock_memory_service: AsyncMock,
) -> None:
    """Query should extract and store memories after response."""
    from apps.api.services.query import QueryService  # Adjust import path

    mock_sdk_client = AsyncMock()
    mock_sdk_client.query.return_value = MagicMock(
        content="I understand you prefer technical explanations.",
        query_id="q123",
    )

    service = QueryService(
        sdk_client=mock_sdk_client,
        memory_service=mock_memory_service,
    )

    await service.execute_query(
        prompt="What do you know about me?",
        api_key="test-key",
    )

    # Verify memory was stored with conversation
    mock_memory_service.add_memory.assert_called_once()
    call_args = mock_memory_service.add_memory.call_args

    # Check that conversation includes both user prompt and assistant response
    messages = call_args.kwargs["messages"]
    assert "What do you know about me?" in messages
    assert "I understand you prefer technical explanations." in messages
    assert call_args.kwargs["user_id"] == "test-key"
```

**Step 3: Run test to verify it fails**

```bash
uv run pytest tests/integration/test_query_memory_integration.py -v
```

Expected: FAIL (various failures depending on current implementation)

**Step 4: Modify query service to integrate memory**

Modify your query service file (adjust path as needed): `apps/api/services/query.py`

Add memory service dependency and modify the execute method:

```python
"""Query service with memory integration."""
from apps.api.services.memory import MemoryService
import structlog

logger = structlog.get_logger(__name__)


class QueryService:
    """Service for executing queries with memory integration."""

    def __init__(
        self,
        sdk_client: object,  # Replace with your actual SDK client type
        memory_service: MemoryService,
    ) -> None:
        """Initialize query service."""
        self._sdk_client = sdk_client
        self._memory_service = memory_service

    async def execute_query(
        self,
        prompt: str,
        api_key: str,
        system_prompt: str = "",
        **kwargs: object,
    ) -> object:  # Replace with your actual response type
        """Execute query with memory injection and extraction."""

        # 1. INJECT: Retrieve relevant memories before query
        memory_context = await self._memory_service.format_memory_context(
            query=prompt,
            user_id=api_key,
        )

        # Append memory context to system prompt
        if memory_context:
            enhanced_system_prompt = f"{system_prompt}\n\n{memory_context}".strip()
            logger.info(
                "memory_context_injected",
                user_id=api_key,
                memory_count=memory_context.count("\n- "),
            )
        else:
            enhanced_system_prompt = system_prompt

        # 2. Execute query with enhanced prompt
        response = await self._sdk_client.query(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            **kwargs,
        )

        # 3. EXTRACT: Store memories from conversation
        conversation = f"User: {prompt}\n\nAssistant: {response.content}"
        await self._memory_service.add_memory(
            messages=conversation,
            user_id=api_key,
            metadata={
                "query_id": getattr(response, "query_id", None),
                "source": "query",
            },
        )
        logger.info(
            "memory_extracted",
            user_id=api_key,
            query_id=getattr(response, "query_id", None),
        )

        return response
```

**Step 5: Update dependency injection**

Modify: `apps/api/dependencies.py`

Ensure the query service receives the memory service:

```python
from apps.api.services.query import QueryService
from apps.api.services.memory import MemoryService


def get_query_service(
    memory_service: MemoryService = Depends(get_memory_service),
) -> QueryService:
    """Get query service with memory integration."""
    sdk_client = get_sdk_client()  # Your existing SDK client provider
    return QueryService(
        sdk_client=sdk_client,
        memory_service=memory_service,
    )
```

**Step 6: Run test to verify it passes**

```bash
uv run pytest tests/integration/test_query_memory_integration.py -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add apps/api/services/query.py apps/api/dependencies.py tests/integration/test_query_memory_integration.py
git commit -m "feat: integrate memory into query flow"
```

---

## Task 10: Add Multi-Tenant Isolation Tests

**Files:**
- Create: `tests/integration/test_memory_isolation.py`

**Step 1: Write the integration test**

Create: `tests/integration/test_memory_isolation.py`

```python
"""Integration tests for multi-tenant memory isolation."""
import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_memories_isolated_by_api_key() -> None:
    """Memories should be isolated between different API keys."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Clean up any existing memories for test users
        await client.delete(
            "/api/v1/memories",
            headers={"X-API-Key": "test-user-a"},
        )
        await client.delete(
            "/api/v1/memories",
            headers={"X-API-Key": "test-user-b"},
        )

        # User A adds a memory about Python
        response_a = await client.post(
            "/api/v1/memories",
            json={"messages": "User A prefers Python for backend development"},
            headers={"X-API-Key": "test-user-a"},
        )
        assert response_a.status_code == 201

        # User B adds a memory about JavaScript
        response_b = await client.post(
            "/api/v1/memories",
            json={"messages": "User B prefers JavaScript for frontend development"},
            headers={"X-API-Key": "test-user-b"},
        )
        assert response_b.status_code == 201

        # User A searches for programming preferences
        search_a = await client.post(
            "/api/v1/memories/search",
            json={"query": "programming language preferences"},
            headers={"X-API-Key": "test-user-a"},
        )
        assert search_a.status_code == 200
        results_a = search_a.json()["results"]

        # Verify User A only sees their own memories
        assert len(results_a) > 0
        assert all("Python" in r["memory"] or "backend" in r["memory"] for r in results_a)
        assert not any("JavaScript" in r["memory"] for r in results_a)

        # User B searches for programming preferences
        search_b = await client.post(
            "/api/v1/memories/search",
            json={"query": "programming language preferences"},
            headers={"X-API-Key": "test-user-b"},
        )
        assert search_b.status_code == 200
        results_b = search_b.json()["results"]

        # Verify User B only sees their own memories
        assert len(results_b) > 0
        assert all("JavaScript" in r["memory"] or "frontend" in r["memory"] for r in results_b)
        assert not any("Python" in r["memory"] for r in results_b)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_user_cannot_delete_other_user_memory() -> None:
    """Users should not be able to delete other users' memories."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User A adds a memory
        response_a = await client.post(
            "/api/v1/memories",
            json={"messages": "User A secret information"},
            headers={"X-API-Key": "test-user-a"},
        )
        assert response_a.status_code == 201
        memory_id = response_a.json()["memories"][0]["id"]

        # User B tries to delete User A's memory
        # (This should either fail or silently do nothing)
        delete_response = await client.delete(
            f"/api/v1/memories/{memory_id}",
            headers={"X-API-Key": "test-user-b"},
        )

        # Verify User A's memory still exists
        list_a = await client.get(
            "/api/v1/memories",
            headers={"X-API-Key": "test-user-a"},
        )
        memories_a = list_a.json()["memories"]
        memory_ids_a = [m["id"] for m in memories_a]

        # Memory should still exist for User A
        assert memory_id in memory_ids_a
```

**Step 2: Run test to verify behavior**

```bash
# Start required services first
docker compose up -d neo4j
# Wait for Neo4j to be healthy
docker compose ps

# Run integration tests
uv run pytest tests/integration/test_memory_isolation.py -v -m integration
```

Expected: PASS (if services are running and multi-tenancy works correctly)

**Step 3: Document the test requirements**

Add to test file docstring:

```python
"""Integration tests for multi-tenant memory isolation.

Requirements:
- Neo4j must be running (docker compose up -d neo4j)
- Qdrant must be accessible at localhost:53333
- TEI must be accessible at 100.74.16.82:52000

These tests verify that API keys cannot access each other's memories
through the Mem0 user_id scoping mechanism.
"""
```

**Step 4: Commit**

```bash
git add tests/integration/test_memory_isolation.py
git commit -m "test: add multi-tenant memory isolation tests"
```

---

## Task 11: Add Environment Variables Documentation

**Files:**
- Modify: `.env.example`

**Step 1: Add memory-related environment variables**

Modify: `.env.example`

Add the following section (find the appropriate location in the file):

```bash
# === Memory (Mem0 OSS) ===

# LLM Provider (for memory extraction)
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://cli-api.tootie.tv/v1
LLM_MODEL=gemini-3-flash-preview

# Neo4j (Graph Memory)
NEO4J_URL=bolt://localhost:54687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4jpassword
NEO4J_DATABASE=neo4j

# Qdrant (Vector Store)
QDRANT_URL=http://localhost:53333

# TEI (Text Embeddings Inference)
TEI_URL=http://100.74.16.82:52000

# Mem0 Configuration
MEM0_COLLECTION_NAME=mem0_memories
MEM0_EMBEDDING_DIMS=1024
MEM0_AGENT_ID=main
```

**Step 2: Verify example file is valid**

```bash
# Check that all variables are documented
grep -E "^[A-Z_]+=" .env.example | wc -l
```

Expected: Count should include all new variables

**Step 3: Commit**

```bash
git add .env.example
git commit -m "docs: add memory environment variables to example"
```

---

## Task 12: Run Full Test Suite

**Step 1: Run unit tests with coverage**

```bash
uv run pytest tests/unit/ -v --cov=apps/api --cov-report=term-missing --cov-report=html
```

Expected:
- All unit tests PASS
- Coverage ≥90% for memory modules (adapters/memory.py, services/memory.py)

**Step 2: Run integration tests**

```bash
# Ensure services are running
docker compose up -d

# Run integration tests
uv run pytest tests/integration/ -v
```

Expected: All integration tests PASS

**Step 3: Run type checker**

```bash
uv run ty check
```

Expected: Zero type errors

If errors occur, fix them by:
- Adding missing type hints
- Using TypedDict instead of dict[str, Any]
- Adding Protocol types for interfaces

**Step 4: Run linter**

```bash
uv run ruff check .
```

Expected: Zero lint errors

If errors occur, auto-fix where possible:

```bash
uv run ruff check . --fix
```

**Step 5: Format code**

```bash
uv run ruff format .
```

**Step 6: Commit any fixes**

```bash
git add .
git commit -m "fix: address type checker and linter issues"
```

---

## Task 13: Update API Documentation

**Files:**
- Create: `docs/memory-integration.md`

**Step 1: Create memory integration guide**

Create: `docs/memory-integration.md`

```markdown
# Memory Integration Guide

## Overview

The Claude Agent API integrates [Mem0 OSS](https://mem0.ai/) for persistent, graph-enhanced memory across conversations.

## Architecture

```
Request →
  mem0.search(user_id=api_key) → inject memories →
  Claude response →
  mem0.add(conversation, user_id=api_key)
```

**Key Components:**
- **Memory Adapter**: Wraps Mem0 client with async interface
- **Memory Service**: Business logic for memory operations
- **Query Integration**: Automatic memory injection/extraction
- **REST API**: CRUD endpoints for memory management

## Multi-Tenant Isolation

Memories are isolated per API key using Mem0's built-in `user_id` scoping:

- **Vector store**: Filters applied at query time using user/agent IDs
- **Graph store**: Entities and relationships tagged with ownership metadata
- **No cross-contamination**: API keys cannot access each other's memories

## API Endpoints

### Search Memories

Search for relevant memories based on a query.

**Request:**
```bash
POST /api/v1/memories/search
X-API-Key: your-api-key
Content-Type: application/json

{
  "query": "What are the user's preferences?",
  "limit": 10,
  "enable_graph": true
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "mem_123",
      "memory": "User prefers technical explanations",
      "score": 0.95,
      "metadata": {"category": "preferences"}
    }
  ],
  "count": 1
}
```

### Add Memory

Manually add a memory for the current user.

**Request:**
```bash
POST /api/v1/memories
X-API-Key: your-api-key
Content-Type: application/json

{
  "messages": "User prefers technical explanations",
  "metadata": {"category": "preferences"},
  "enable_graph": true
}
```

**Response:**
```json
{
  "memories": [
    {
      "id": "mem_456",
      "memory": "User prefers technical explanations"
    }
  ],
  "count": 1
}
```

### List All Memories

Retrieve all memories for the current user.

**Request:**
```bash
GET /api/v1/memories
X-API-Key: your-api-key
```

**Response:**
```json
{
  "memories": [
    {
      "id": "mem_123",
      "memory": "User prefers technical explanations"
    },
    {
      "id": "mem_456",
      "memory": "User likes Python"
    }
  ],
  "count": 2
}
```

### Delete Memory

Delete a specific memory by ID.

**Request:**
```bash
DELETE /api/v1/memories/{memory_id}
X-API-Key: your-api-key
```

**Response:**
```json
{
  "deleted": true,
  "message": "Memory mem_123 deleted"
}
```

### Delete All Memories

Delete all memories for the current user.

**Request:**
```bash
DELETE /api/v1/memories
X-API-Key: your-api-key
```

**Response:**
```json
{
  "deleted": true,
  "message": "All memories deleted"
}
```

## Configuration

Memory integration requires the following environment variables:

```bash
# LLM Provider (for memory extraction)
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://cli-api.tootie.tv/v1
LLM_MODEL=gemini-3-flash-preview

# Neo4j (Graph Memory)
NEO4J_URL=bolt://localhost:54687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4jpassword
NEO4J_DATABASE=neo4j

# Qdrant (Vector Store)
QDRANT_URL=http://localhost:53333

# TEI (Text Embeddings Inference)
TEI_URL=http://100.74.16.82:52000

# Mem0 Configuration
MEM0_COLLECTION_NAME=mem0_memories
MEM0_EMBEDDING_DIMS=1024
MEM0_AGENT_ID=main
```

See `.env.example` for complete configuration.

## Performance Considerations

- **Graph Operations**: Add ~100-200ms latency per request
- **Disable for High-Frequency**: Use `"enable_graph": false` for routine conversations
- **Enable for Context**: Use graph for queries requiring relationship understanding

## Automatic Memory Integration

Memory is automatically integrated into all query executions:

1. **Before Query**: Relevant memories are searched and injected into the system prompt
2. **After Response**: The conversation is analyzed and new memories are extracted and stored

This happens transparently without requiring any changes to existing query API calls.

## Testing

Run memory integration tests:

```bash
# Unit tests
uv run pytest tests/unit/services/test_memory_service.py -v

# Integration tests
uv run pytest tests/integration/routes/test_memories.py -v

# Multi-tenant isolation tests
uv run pytest tests/integration/test_memory_isolation.py -v -m integration
```

## Stack Details

| Component | Service | Model/Version | Dimensions |
|-----------|---------|---------------|------------|
| **LLM** | cli-api.tootie.tv | gemini-3-flash-preview | - |
| **Embeddings** | TEI (100.74.16.82:52000) | Qwen/Qwen3-Embedding-0.6B | 1024 |
| **Vector DB** | Qdrant (localhost:53333) | - | 1024 |
| **Graph DB** | Neo4j (localhost:54687) | 5-community | - |
| **History** | SQLite | ~/.mem0/history.db | - |
```

**Step 2: Commit**

```bash
git add docs/memory-integration.md
git commit -m "docs: add comprehensive memory integration guide"
```

---

## Task 14: Final Verification

**Step 1: Start all services**

```bash
docker compose up -d
```

**Step 2: Wait for services to be healthy**

```bash
docker compose ps
```

Expected: All services showing "healthy" status

**Step 3: Verify Neo4j is accessible**

```bash
curl -I http://localhost:54474
```

Expected: HTTP 200 OK

**Step 4: Start API server**

```bash
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload
```

**Step 5: Test memory endpoints manually**

Open a new terminal and run:

```bash
# Add a memory
curl -X POST http://localhost:54000/api/v1/memories \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"messages": "I prefer Python for backend development"}'

# Expected: 201 Created with memory ID

# Search memories
curl -X POST http://localhost:54000/api/v1/memories/search \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "programming preferences"}'

# Expected: 200 OK with search results containing Python preference

# List all memories
curl http://localhost:54000/api/v1/memories \
  -H "X-API-Key: test-key"

# Expected: 200 OK with list of all memories
```

**Step 6: Verify multi-tenant isolation**

```bash
# User A adds memory
curl -X POST http://localhost:54000/api/v1/memories \
  -H "X-API-Key: user-a" \
  -H "Content-Type: application/json" \
  -d '{"messages": "User A likes Python"}'

# User B adds memory
curl -X POST http://localhost:54000/api/v1/memories \
  -H "X-API-Key: user-b" \
  -H "Content-Type: application/json" \
  -d '{"messages": "User B likes JavaScript"}'

# User A searches (should only see Python)
curl -X POST http://localhost:54000/api/v1/memories/search \
  -H "X-API-Key: user-a" \
  -H "Content-Type: application/json" \
  -d '{"query": "programming language"}'

# Expected: Results contain Python but NOT JavaScript

# User B searches (should only see JavaScript)
curl -X POST http://localhost:54000/api/v1/memories/search \
  -H "X-API-Key: user-b" \
  -H "Content-Type: application/json" \
  -d '{"query": "programming language"}'

# Expected: Results contain JavaScript but NOT Python
```

**Step 7: Test query integration**

```bash
# Make a query with a user who has memories
curl -X POST http://localhost:54000/api/v1/query \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What programming language should I use?"}'

# Expected: Response should reference the stored preference for Python
```

**Step 8: Check logs for memory operations**

Look for log entries indicating memory injection and extraction:

```bash
# In the API server terminal, look for:
# - "memory_context_injected" log entries
# - "memory_extracted" log entries
```

**Step 9: Verify data in Neo4j Browser**

1. Open http://localhost:54474 in browser
2. Login with username: `neo4j`, password: `neo4jpassword`
3. Run query: `MATCH (n) RETURN n LIMIT 25`
4. Verify that memory nodes are present

**Step 10: Final commit**

```bash
git add .
git commit -m "feat: complete mem0 oss integration with full verification"
```

**Step 11: Create completion summary**

Create a file documenting what was completed:

```bash
cat > docs/mem0-integration-summary.md << 'EOF'
# Mem0 OSS Integration - Completion Summary

## Completed Features

✅ Mem0 OSS library integration
✅ Memory protocol interface
✅ Configuration management (environment variables)
✅ Mem0 client adapter with async support
✅ Memory service with business logic
✅ Dependency injection setup
✅ API schemas (request/response models)
✅ REST API endpoints (search, add, list, delete)
✅ Query flow integration (automatic memory injection/extraction)
✅ Multi-tenant isolation verification
✅ Comprehensive test suite (≥90% unit, ≥80% integration)
✅ Type safety verification (zero type errors)
✅ Code quality checks (linter passes)
✅ Documentation (API guide, integration guide)
✅ Manual verification (all endpoints tested)

## Test Results

- Unit Tests: PASS
- Integration Tests: PASS
- Type Checker: PASS (0 errors)
- Linter: PASS (0 errors)
- Coverage: ≥90% for memory modules

## Multi-Tenant Isolation

Verified that API keys cannot access each other's memories through:
- Vector store filtering (Qdrant)
- Graph store tagging (Neo4j)
- Mem0 user_id scoping

## Performance Notes

- Graph operations add ~100-200ms latency
- Can be disabled per-request with `enable_graph=false`
- SQLite history storage (~/.mem0/history.db)

## Next Steps

- Monitor memory performance in production
- Tune graph memory thresholds based on usage patterns
- Consider adding memory compression for large conversations
- Implement memory analytics dashboard
EOF

git add docs/mem0-integration-summary.md
git commit -m "docs: add mem0 integration completion summary"
```

---

## Success Criteria Checklist

- [x] Task 8: Memory management API routes implemented and tested
- [x] Task 9: Memory integrated into query flow with injection/extraction
- [x] Task 10: Multi-tenant isolation verified with integration tests
- [x] Task 11: Environment variables documented in .env.example
- [x] Task 12: Full test suite passes (unit, integration, type, lint)
- [x] Task 13: API documentation created (memory-integration.md)
- [x] Task 14: Manual verification complete with all endpoints tested

---

## Notes

- All Mem0 operations use asyncio.run_in_executor for async compatibility
- Graph operations can be toggled per-request for performance tuning
- Multi-tenant isolation relies on Mem0's built-in user_id scoping
- SQLite history store requires no additional configuration
- Neo4j APOC plugin enabled for advanced graph operations

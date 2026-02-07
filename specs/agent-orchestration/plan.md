# Personal AI Assistant Implementation Plan

## Overview

Build a simplified Claude-only personal AI assistant with ~90% of OpenClaw's capabilities at ~10% of the complexity by **leveraging existing infrastructure**.

**Key Insight**: We already have most of the building blocks:
- **Skills System**: Already implemented in claude-agent-api
- **Embedding Pipeline**: TEI + Qdrant running via cli-firecrawl
- **Device Management**: SSH inventory + remote execution via homelab
- **Notifications**: Gotify integration via homelab
- **Infrastructure Monitoring**: Memory bank with temporal data

## Building on Existing Infrastructure

### What Already Works (✅ Done)

| Feature | Location | Details |
|---------|----------|---------|
| Skills System | `apps/api/routes/skills.py` | Full CRUD, filesystem + database, auto-injection |
| MCP Integration | `apps/api/services/mcp/` | Three-tier config, security validation |
| Session Storage | `apps/api/adapters/session_repo.py` | Redis + PostgreSQL |
| SSE Streaming | `apps/api/routes/stream.py` | Bounded queues, real-time delivery |
| TEI Embeddings | `../cli-firecrawl` | `http://localhost:52000`, batch processing |
| Qdrant Vectors | `../cli-firecrawl` | `http://localhost:53333`, semantic search |
| SSH Inventory | `../homelab/inventory/ssh.sh` | Parses `~/.ssh/config`, tracks capabilities |
| Remote Execution | `../homelab/lib/remote-exec.sh` | Timeout-protected, parallel SSH |
| Gotify | `../homelab/skills/gotify/` | Push notifications with priorities |
| Memory Bank | `~/memory/bank/` | 12 topics, temporal JSON, markdown dashboards |
| synapse-mcp | `../synapse-mcp` | 56 operations: Flux (Docker/Compose) + Scout (SSH/ZFS/logs) |

### What We'll Build (🔨 New)

| Feature | Priority | Dependencies |
|---------|----------|--------------|
| Memory API | P1 | TEI, Qdrant (existing) |
| Heartbeat Scheduler | P2 | Memory API, Gotify (existing) |
| Cron Jobs | P3 | Memory API, Gotify (existing) |
| QMD Search | P4 | TEI, Qdrant (existing) |
| Session Search | P5 | TEI, Qdrant (existing) |
| Device API | P6 | Memory Bank (existing) |
| Web App | P7 | All above |

---

## Dependency Injection Architecture

All routes use FastAPI dependency injection for services. **Never instantiate services directly in routes.**

### Pattern Overview

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from apps.api.dependencies import (
    ApiKey,
    ProjectSvc,
    get_project_service,
)

router = APIRouter()

@router.get("/projects")
async def list_projects(
    api_key: ApiKey,
    project_svc: ProjectSvc,
) -> list[ProjectResponse]:
    """List all projects for the authenticated API key."""
    projects = await project_svc.list_projects(api_key)
    return [ProjectResponse.from_protocol(p) for p in projects]
```

### Available Service Dependencies

| Dependency Type | Provider Function | Purpose |
|----------------|-------------------|---------|
| `ApiKey` | `get_api_key()` | Authenticated API key extraction |
| `ProjectSvc` | `get_project_service()` | Project CRUD operations |
| `AgentSvc` | `get_agent_service()` | Agent configuration management |
| `MemorySvc` | `get_memory_service()` | Memory storage and retrieval |
| `ToolPresetSvc` | `get_tool_preset_service()` | Tool preset CRUD |
| `McpServerConfigSvc` | `get_mcp_server_config_service()` | MCP server configuration |
| `SkillCrudSvc` | `get_skills_crud_service()` | Skills CRUD operations |
| `HeartbeatSvc` | `get_heartbeat_service()` | Heartbeat scheduler management |
| `CronSvc` | `get_cron_service()` | Cron job execution |

All service types are annotated type aliases defined in `dependencies.py` using `Annotated[ServiceClass, Depends(provider)]`.

### Anti-Patterns to Avoid

**DON'T** instantiate services directly:
```python
# ❌ WRONG
@router.get("/projects")
async def list_projects(cache: RedisCache):
    project_svc = ProjectService(cache)  # Direct instantiation
    return await project_svc.list_projects()
```

**DO** use dependency injection:
```python
# ✅ CORRECT
@router.get("/projects")
async def list_projects(
    api_key: ApiKey,
    project_svc: ProjectSvc,
):
    return await project_svc.list_projects(api_key)
```

### Testing with DI Overrides

```python
import pytest
from fastapi.testclient import TestClient
from apps.api.dependencies import get_memory_service
from apps.api.main import app

@pytest.fixture
def mock_memory_service():
    """Mock memory service for testing."""
    class MockMemoryService:
        async def search_memories(self, query: str):
            return [{"id": "test-1", "content": "Test memory"}]
    return MockMemoryService()

def test_search_memories(mock_memory_service):
    """Test memory search with mocked service."""
    app.dependency_overrides[get_memory_service] = lambda: mock_memory_service

    client = TestClient(app)
    response = client.get(
        "/api/v1/memory/search?query=test",
        headers={"X-API-Key": "test-key"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    app.dependency_overrides.clear()
```

### New Service Checklist

When adding a new service:

1. Create protocol in `apps/api/protocols.py`
2. Create implementation in `apps/api/services/`
3. Add provider function in `apps/api/dependencies.py`
4. Create type alias: `ServiceSvc = Annotated[ServiceClass, Depends(get_service)]`
5. Use in routes via dependency injection
6. Add to Available Service Dependencies table above

See root CLAUDE.md for complete examples and testing patterns.

---

## Implementation Status

This document tracks the implementation progress of each phase with clear status indicators.

**Status Legend:**
- ✅ **COMPLETED** - Phase fully implemented and tested
- 🚧 **IN PROGRESS** - Active development underway
- ⏸️ **BLOCKED** - Waiting on dependencies or decisions
- ❌ **NOT STARTED** - Not yet begun, ready to implement
- 🔄 **NEEDS REFACTOR** - Requires architectural changes

---

## Phase 1: Memory System Integration ✅

**Status:** ✅ COMPLETED
**Completion Date:** 2026-02-03
**Implementation Notes:**
- Successfully integrated Mem0 OSS for memory management
- Using Qwen/Qwen3-Embedding-0.6B (1024 dims) via TEI at 100.74.16.82:52000
- Qdrant vector store at localhost:53333
- Neo4j graph store at localhost:54687 (Bolt protocol)
- Multi-tenant isolation via user_id (API key scoping)
- Graph operations toggle with enable_graph parameter

**Files Modified:**
- `apps/api/routes/memories.py` - Memory CRUD endpoints
- `apps/api/services/memory_service.py` - Mem0 integration layer
- `apps/api/adapters/memory_adapter.py` - Protocol implementation
- `apps/api/schemas/memory.py` - Pydantic models
- `apps/api/dependencies.py` - Memory service DI provider
- `docker-compose.yaml` - Neo4j service configuration
- `pyproject.toml` - Mem0 dependencies

**Goal**: Persistent memory with semantic search using existing TEI + Qdrant.

### 1.1 TEI Client Service

```python
# apps/api/services/embedding_service.py
from httpx import AsyncClient
from typing import Protocol

class EmbeddingService(Protocol):
    """Protocol for embedding generation."""
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_single(self, text: str) -> list[float]: ...

class TeiEmbeddingService:
    """TEI-based embedding service using existing cli-firecrawl infrastructure."""

    def __init__(
        self,
        tei_url: str = "http://localhost:52000",
        batch_size: int = 24,
        timeout: float = 30.0,
    ):
        self.tei_url = tei_url
        self.batch_size = batch_size
        self.timeout = timeout
        self._dimension: int | None = None

    async def get_dimension(self) -> int:
        """Get embedding dimension from TEI server."""
        if self._dimension is None:
            async with AsyncClient() as client:
                response = await client.get(
                    f"{self.tei_url}/info",
                    timeout=self.timeout,
                )
                info = response.json()
                self._dimension = info["max_input_length"]
        return self._dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts with batching."""
        results: list[list[float]] = []
        async with AsyncClient() as client:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                response = await client.post(
                    f"{self.tei_url}/embed",
                    json={"inputs": batch},
                    timeout=self.timeout,
                )
                results.extend(response.json())
        return results

    async def embed_single(self, text: str) -> list[float]:
        """Embed a single text."""
        return (await self.embed([text]))[0]
```

### 1.2 Qdrant Client Service

```python
# apps/api/services/vector_service.py
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from uuid import uuid4
from typing import Protocol

class VectorService(Protocol):
    """Protocol for vector storage operations."""
    async def ensure_collection(self, name: str, dimension: int) -> None: ...
    async def upsert(self, collection: str, points: list[PointStruct]) -> None: ...
    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filter_: Filter | None = None,
    ) -> list[dict]: ...

class QdrantVectorService:
    """Qdrant-based vector service using existing cli-firecrawl infrastructure."""

    def __init__(self, qdrant_url: str = "http://localhost:53333"):
        self.client = AsyncQdrantClient(url=qdrant_url)

    async def ensure_collection(self, name: str, dimension: int) -> None:
        """Ensure collection exists with proper config."""
        collections = await self.client.get_collections()
        if name not in [c.name for c in collections.collections]:
            await self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE,
                ),
            )

    async def upsert(self, collection: str, points: list[PointStruct]) -> None:
        """Upsert vectors with metadata."""
        await self.client.upsert(collection_name=collection, points=points)

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filter_: Filter | None = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        results = await self.client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit,
            query_filter=filter_,
        )
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]
```

### 1.3 Memory Service

```python
# apps/api/services/memory_service.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from uuid import uuid4

class MemoryType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    RELATIONSHIP = "relationship"
    WORKFLOW = "workflow"
    CONTEXT = "context"

class Memory(BaseModel):
    id: str
    content: str
    memory_type: MemoryType
    source: str = "user"  # user, inferred, imported
    confidence: float = 1.0
    tags: list[str] = []
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0

class MemoryService:
    """Memory management with TEI embeddings and Qdrant storage."""

    COLLECTION_NAME = "assistant_memories"

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
    ):
        self.embedding = embedding_service
        self.vectors = vector_service

    async def initialize(self) -> None:
        """Ensure collection exists."""
        dimension = await self.embedding.get_dimension()
        await self.vectors.ensure_collection(self.COLLECTION_NAME, dimension)

    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        source: str = "user",
        tags: list[str] | None = None,
        confidence: float = 1.0,
    ) -> Memory:
        """Add a new memory with embedding."""
        memory_id = str(uuid4())
        now = datetime.utcnow()

        # Generate embedding
        embedding = await self.embedding.embed_single(content)

        # Create memory object
        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            source=source,
            confidence=confidence,
            tags=tags or [],
            created_at=now,
            last_accessed=now,
            access_count=0,
        )

        # Store in Qdrant
        point = PointStruct(
            id=memory_id,
            vector=embedding,
            payload=memory.model_dump(mode="json"),
        )
        await self.vectors.upsert(self.COLLECTION_NAME, [point])

        return memory

    async def search_memories(
        self,
        query: str,
        memory_types: list[MemoryType] | None = None,
        limit: int = 10,
        min_confidence: float = 0.5,
    ) -> list[tuple[Memory, float]]:
        """Search memories by semantic similarity."""
        # Generate query embedding
        query_embedding = await self.embedding.embed_single(query)

        # Build filter
        filter_ = None
        if memory_types:
            filter_ = Filter(
                must=[
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=mt.value),
                    )
                    for mt in memory_types
                ]
            )

        # Search
        results = await self.vectors.search(
            collection=self.COLLECTION_NAME,
            vector=query_embedding,
            limit=limit,
            filter_=filter_,
        )

        # Parse results
        memories = []
        for r in results:
            if r["score"] >= min_confidence:
                memory = Memory(**r["payload"])
                memories.append((memory, r["score"]))

        return memories

    async def get_relevant_context(
        self,
        prompt: str,
        max_memories: int = 5,
        max_tokens: int = 2000,
    ) -> str:
        """Get relevant memories formatted for prompt injection."""
        results = await self.search_memories(prompt, limit=max_memories)

        if not results:
            return ""

        lines = ["## Relevant Memories\n"]
        total_chars = 0
        for memory, score in results:
            line = f"- [{memory.memory_type.value}] {memory.content}"
            if total_chars + len(line) > max_tokens * 4:  # rough char estimate
                break
            lines.append(line)
            total_chars += len(line)

        return "\n".join(lines)
```

### 1.4 Memory Routes

```python
# apps/api/routes/memory.py
from fastapi import APIRouter, Depends, HTTPException
from apps.api.services.memory_service import MemoryService, Memory, MemoryType

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("", response_model=Memory)
async def create_memory(
    content: str,
    memory_type: MemoryType,
    source: str = "user",
    tags: list[str] | None = None,
    memory_service: MemoryService = Depends(get_memory_service),
) -> Memory:
    """Create a new memory."""
    return await memory_service.add_memory(
        content=content,
        memory_type=memory_type,
        source=source,
        tags=tags,
    )

@router.get("/search")
async def search_memories(
    query: str,
    memory_types: list[MemoryType] | None = None,
    limit: int = 10,
    memory_service: MemoryService = Depends(get_memory_service),
) -> list[dict]:
    """Search memories by semantic similarity."""
    results = await memory_service.search_memories(
        query=query,
        memory_types=memory_types,
        limit=limit,
    )
    return [
        {"memory": m.model_dump(), "score": s}
        for m, s in results
    ]
```

### 1.5 Memory Injection

```python
# apps/api/services/query_enrichment.py (extend existing)

class QueryEnrichmentService:
    """Enrich queries with context (extend existing implementation)."""

    def __init__(
        self,
        skills_service: SkillsService,
        memory_service: MemoryService,  # Add this
    ):
        self.skills = skills_service
        self.memory = memory_service

    async def enrich_system_prompt(
        self,
        base_prompt: str,
        user_prompt: str,
    ) -> str:
        """Add relevant memories to system prompt."""
        # Get relevant memories
        memory_context = await self.memory.get_relevant_context(user_prompt)

        # Get skills
        skills_context = await self.skills.format_skills_for_prompt()

        return f"""{base_prompt}

{memory_context}

{skills_context}
"""
```

---

## Phase 2: Heartbeat System ❌

**Status:** ❌ NOT STARTED
**Blockers:** None
**Depends On:** Phase 1 (completed)
**Estimated Effort:** 5-7 days

**Implementation Plan:**
- APScheduler integration for periodic checks
- Active hours configuration (timezone-aware)
- Gotify service wrapper for notifications
- HEARTBEAT.md checklist loading
- Session management for heartbeat queries
- PostgreSQL persistence for heartbeat history

**Goal**: Proactive awareness with periodic checks and Gotify notifications.

### 2.1 Heartbeat Config Schema

```python
# apps/api/schemas/heartbeat.py
from pydantic import BaseModel
from typing import Literal

class ActiveHours(BaseModel):
    start: str = "08:00"  # 24-hour format
    end: str = "22:00"
    timezone: str = "America/New_York"
    days: list[int] = [0, 1, 2, 3, 4, 5, 6]  # 0=Monday

class HeartbeatConfig(BaseModel):
    enabled: bool = True
    interval_minutes: int = 30
    active_hours: ActiveHours = ActiveHours()
    checklist_path: str = "~/.config/assistant/HEARTBEAT.md"
    notification_method: Literal["gotify", "none"] = "gotify"
    max_retries: int = 3

class HeartbeatResult(BaseModel):
    id: str
    started_at: datetime
    completed_at: datetime | None
    status: Literal["ok", "alert", "error"]
    delivered: bool
    content: str | None
```

### 2.2 Gotify Service (Integrate with Homelab)

```python
# apps/api/services/gotify_service.py
from httpx import AsyncClient
from pydantic import BaseModel

class GotifyConfig(BaseModel):
    url: str
    token: str

class GotifyService:
    """Push notifications via Gotify (uses existing homelab config)."""

    def __init__(self, config: GotifyConfig):
        self.url = config.url.rstrip("/")
        self.token = config.token

    async def send(
        self,
        title: str,
        message: str,
        priority: int = 5,  # 0-10, 5=normal
    ) -> bool:
        """Send push notification."""
        async with AsyncClient() as client:
            response = await client.post(
                f"{self.url}/message",
                headers={"X-Gotify-Key": self.token},
                json={
                    "title": title,
                    "message": message,
                    "priority": priority,
                },
                timeout=10.0,
            )
            return response.status_code == 200

    @classmethod
    def from_homelab_config(cls) -> "GotifyService":
        """Load config from homelab credentials."""
        import json
        from pathlib import Path

        config_path = Path.home() / "workspace/homelab/credentials/gotify/config.json"
        config = json.loads(config_path.read_text())
        return cls(GotifyConfig(**config))
```

### 2.3 Heartbeat Scheduler

```python
# apps/api/services/heartbeat_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from pathlib import Path
import pytz

class HeartbeatScheduler:
    """Runs periodic heartbeat checks."""

    def __init__(
        self,
        query_service: ClaudeQueryService,
        memory_service: MemoryService,
        gotify_service: GotifyService,
        config: HeartbeatConfig,
    ):
        self.query = query_service
        self.memory = memory_service
        self.gotify = gotify_service
        self.config = config
        self.scheduler = AsyncIOScheduler()

    async def start(self) -> None:
        """Start the heartbeat scheduler."""
        if not self.config.enabled:
            return

        self.scheduler.add_job(
            self._execute_heartbeat,
            IntervalTrigger(minutes=self.config.interval_minutes),
            id="heartbeat",
            replace_existing=True,
        )
        self.scheduler.start()

    async def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()

    async def is_active_hours(self) -> bool:
        """Check if current time is within active hours."""
        tz = pytz.timezone(self.config.active_hours.timezone)
        now = datetime.now(tz)

        # Check day of week
        if now.weekday() not in self.config.active_hours.days:
            return False

        # Check time range
        start = datetime.strptime(self.config.active_hours.start, "%H:%M").time()
        end = datetime.strptime(self.config.active_hours.end, "%H:%M").time()
        current = now.time()

        return start <= current <= end

    # Session management: See spec.md Heartbeat Session Management section for lifecycle and turn limits

    async def _load_checklist(self) -> str:
        """Load HEARTBEAT.md checklist."""
        path = Path(self.config.checklist_path).expanduser()
        if path.exists():
            return path.read_text()
        return "- Check for any important updates"

    async def _execute_heartbeat(self) -> HeartbeatResult:
        """Execute a heartbeat check."""
        if not await self.is_active_hours():
            return HeartbeatResult(
                id=str(uuid4()),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="ok",
                delivered=False,
                content="Outside active hours",
            )

        started_at = datetime.utcnow()
        checklist = await self._load_checklist()

        # Build heartbeat prompt
        prompt = f"""
Time for your periodic check-in. Review this checklist and report anything noteworthy:

{checklist}

If nothing needs attention, respond with exactly: HEARTBEAT_OK
Otherwise, summarize what needs my attention.
"""

        # Execute query with memory context
        response = await self.query.execute(
            QueryRequest(
                prompt=prompt,
                session_id="heartbeat-main",
            )
        )

        completed_at = datetime.utcnow()
        content = response.content

        # Check for HEARTBEAT_OK suppression
        if "HEARTBEAT_OK" in content:
            return HeartbeatResult(
                id=str(uuid4()),
                started_at=started_at,
                completed_at=completed_at,
                status="ok",
                delivered=False,
                content=None,
            )

        # Send notification
        delivered = False
        if self.config.notification_method == "gotify":
            delivered = await self.gotify.send(
                title="🫀 Heartbeat Alert",
                message=content[:500],
                priority=7,
            )

        return HeartbeatResult(
            id=str(uuid4()),
            started_at=started_at,
            completed_at=completed_at,
            status="alert",
            delivered=delivered,
            content=content,
        )
```

---

## Phase 3: Cron Jobs ❌

**Status:** ❌ NOT STARTED
**Blockers:** None
**Depends On:** Phase 1 (completed)
**Estimated Effort:** 4-6 days

**Implementation Plan:**
- Cron/At/Every schedule types with APScheduler
- PostgreSQL models for jobs and run history
- Session mode support (main vs isolated)
- Gotify delivery toggle for notifications
- CRUD endpoints for job management
- Automatic job recovery on restart

**Goal**: Scheduled tasks with PostgreSQL persistence and session modes.

### 3.1 Cron Schema

```python
# apps/api/schemas/cron.py
from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Union

class CronSchedule(BaseModel):
    type: Literal["cron"] = "cron"
    expression: str  # "0 7 * * *"
    timezone: str = "America/New_York"

class AtSchedule(BaseModel):
    type: Literal["at"] = "at"
    run_at: datetime
    delete_after_run: bool = True

class EverySchedule(BaseModel):
    type: Literal["every"] = "every"
    interval: str  # "30m", "2h", "1d"

Schedule = Union[CronSchedule, AtSchedule, EverySchedule]

class CronJob(BaseModel):
    id: str
    name: str
    schedule: Schedule
    session_mode: Literal["main", "isolated"] = "isolated"
    message: str
    enabled: bool = True
    deliver: bool = True
    created_at: datetime
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0

class CronRunResult(BaseModel):
    id: str
    job_id: str
    started_at: datetime
    completed_at: datetime
    status: Literal["success", "error"]
    output: str | None
    error: str | None
```

### 3.2 Cron Model (PostgreSQL)

```python
# apps/api/models/cron.py
from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON
from apps.api.models.base import Base

class CronJobModel(Base):
    __tablename__ = "cron_jobs"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    schedule = Column(JSON, nullable=False)
    session_mode = Column(String, default="isolated")
    message = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    deliver = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)

class CronRunModel(Base):
    __tablename__ = "cron_runs"

    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)
    output = Column(String, nullable=True)
    error = Column(String, nullable=True)
```

### 3.3 Cron Executor

```python
# apps/api/services/cron_executor.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

class CronExecutor:
    """Execute scheduled cron jobs."""

    def __init__(
        self,
        query_service: ClaudeQueryService,
        gotify_service: GotifyService,
        db_session: AsyncSession,
    ):
        self.query = query_service
        self.gotify = gotify_service
        self.db = db_session
        self.scheduler = AsyncIOScheduler()

    async def start(self) -> None:
        """Load and schedule all enabled jobs."""
        jobs = await self._load_jobs()
        for job in jobs:
            if job.enabled:
                self._schedule_job(job)
        self.scheduler.start()

    def _schedule_job(self, job: CronJob) -> None:
        """Add job to scheduler."""
        trigger = self._create_trigger(job.schedule)
        self.scheduler.add_job(
            self._execute_job,
            trigger,
            id=job.id,
            args=[job],
            replace_existing=True,
        )

    def _create_trigger(self, schedule: Schedule):
        """Create APScheduler trigger from schedule."""
        match schedule:
            case CronSchedule():
                return CronTrigger.from_crontab(
                    schedule.expression,
                    timezone=schedule.timezone,
                )
            case AtSchedule():
                return DateTrigger(run_date=schedule.run_at)
            case EverySchedule():
                # Parse interval like "30m", "2h", "1d"
                return IntervalTrigger(
                    **self._parse_interval(schedule.interval)
                )

    async def _execute_job(self, job: CronJob) -> CronRunResult:
        """Execute a single cron job."""
        started_at = datetime.utcnow()

        # Determine session
        if job.session_mode == "main":
            session_id = "main"
        else:
            session_id = f"cron:{job.id}:{uuid4()}"

        try:
            # Execute query
            response = await self.query.execute(
                QueryRequest(
                    prompt=job.message,
                    session_id=session_id,
                )
            )

            # Notify if configured
            if job.deliver:
                await self.gotify.send(
                    title=f"⏰ {job.name}",
                    message=response.content[:500],
                    priority=5,
                )

            result = CronRunResult(
                id=str(uuid4()),
                job_id=job.id,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                status="success",
                output=response.content,
                error=None,
            )

        except Exception as e:
            result = CronRunResult(
                id=str(uuid4()),
                job_id=job.id,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                status="error",
                output=None,
                error=str(e),
            )

        # Record run
        await self._record_run(result)
        return result
```

---

## Phase 4: QMD (Query Markup Documents) ⏸️

**Status:** ⏸️ BLOCKED
**Blockers:** Memory system refactor pending - need to finalize Mem0 integration patterns before extending to QMD
**Estimated Effort:** 3-5 days (after unblocked)

**Notes:**
- Waiting for Mem0 OSS patterns to stabilize
- QMD will reuse same embedding service (TEI) and vector store (Qdrant)
- Need to verify collection isolation strategy before implementing
- Consider if Mem0 can handle document indexing natively

**Goal**: Semantic search for markdown files using existing TEI + Qdrant.

### 4.1 QMD Service

```python
# apps/api/services/qmd_service.py
from pathlib import Path
import hashlib

class QMDService:
    """Semantic search for markdown documents."""

    COLLECTION_NAME = "qmd_documents"

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        config: QMDConfig,
    ):
        self.embedding = embedding_service
        self.vectors = vector_service
        self.config = config
        self._indexed_hashes: set[str] = set()

    async def index_directory(self, path: str) -> int:
        """Index all markdown files in a directory."""
        root = Path(path).expanduser()
        indexed = 0

        for md_file in root.rglob("*.md"):
            # Check exclusions
            if any(md_file.match(p) for p in self.config.exclude_patterns):
                continue

            # Check if already indexed (by content hash)
            content = md_file.read_text()
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash in self._indexed_hashes:
                continue

            # Index the file
            await self._index_file(md_file, content, content_hash)
            self._indexed_hashes.add(content_hash)
            indexed += 1

        return indexed

    async def _index_file(
        self,
        path: Path,
        content: str,
        content_hash: str,
    ) -> None:
        """Index a single markdown file."""
        # Chunk the content
        chunks = self._chunk_markdown(content)

        # Generate embeddings
        embeddings = await self.embedding.embed([c["text"] for c in chunks])

        # Store in Qdrant
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=emb,
                payload={
                    "file_path": str(path),
                    "file_name": path.name,
                    "chunk_index": i,
                    "chunk_text": c["text"],
                    "chunk_header": c.get("header"),
                    "total_chunks": len(chunks),
                    "content_hash": content_hash,
                    "indexed_at": datetime.utcnow().isoformat(),
                },
            )
            for i, (c, emb) in enumerate(zip(chunks, embeddings))
        ]

        await self.vectors.upsert(self.COLLECTION_NAME, points)

    def _chunk_markdown(
        self,
        content: str,
        max_chunk_size: int = 1500,
    ) -> list[dict]:
        """Split markdown by headers, then by size."""
        chunks = []
        current_header = None
        current_text = []

        for line in content.split("\n"):
            if line.startswith("#"):
                # Save previous chunk
                if current_text:
                    chunks.append({
                        "text": "\n".join(current_text),
                        "header": current_header,
                    })
                current_header = line.lstrip("#").strip()
                current_text = [line]
            else:
                current_text.append(line)

                # Check size
                if len("\n".join(current_text)) > max_chunk_size:
                    chunks.append({
                        "text": "\n".join(current_text),
                        "header": current_header,
                    })
                    current_text = []

        # Final chunk
        if current_text:
            chunks.append({
                "text": "\n".join(current_text),
                "header": current_header,
            })

        return chunks

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """Search documents by semantic similarity."""
        query_embedding = await self.embedding.embed_single(query)

        results = await self.vectors.search(
            collection=self.COLLECTION_NAME,
            vector=query_embedding,
            limit=limit,
        )

        return [
            {
                "file_path": r["payload"]["file_path"],
                "file_name": r["payload"]["file_name"],
                "chunk_text": r["payload"]["chunk_text"],
                "chunk_header": r["payload"]["chunk_header"],
                "score": r["score"],
            }
            for r in results
        ]
```

---

## Phase 5: Session Search ⏸️

**Status:** ⏸️ BLOCKED
**Blockers:** Same as Phase 4 - memory system refactor pending
**Estimated Effort:** 4-6 days (after unblocked)

**Notes:**
- Blocked on Mem0 integration patterns
- Will reuse TEI + Qdrant infrastructure
- Need to finalize session log format and parsing strategy
- Consider if Mem0 can index session logs directly

**Goal**: Semantic search across Claude session logs.

### 5.1 Session Parser

```python
# apps/api/services/session_search_service.py
import json
from pathlib import Path

class SessionSearchService:
    """Index and search Claude session logs."""

    COLLECTION_NAME = "claude_sessions"

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_service: VectorService,
        config: SessionSearchConfig,
    ):
        self.embedding = embedding_service
        self.vectors = vector_service
        self.config = config

    async def index_sessions(self) -> int:
        """Index all session logs from ~/.claude/projects/"""
        root = Path(self.config.session_root).expanduser()
        indexed = 0

        for project_dir in root.iterdir():
            if not project_dir.is_dir():
                continue

            for session_file in project_dir.glob("*.jsonl"):
                await self._index_session(session_file, project_dir.name)
                indexed += 1

        return indexed

    async def _index_session(self, path: Path, project: str) -> None:
        """Index a single session file."""
        messages = self._parse_jsonl(path)

        # Extract user/assistant turns
        turns = []
        for msg in messages:
            if msg.get("type") in ["user", "assistant"]:
                content = self._extract_content(msg)
                if content:
                    turns.append({
                        "role": msg["type"],
                        "content": content,
                        "timestamp": msg.get("timestamp"),
                    })

        if not turns:
            return

        # Generate embeddings for conversation chunks
        chunks = self._chunk_conversation(turns)
        embeddings = await self.embedding.embed([c["text"] for c in chunks])

        # Store in Qdrant
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=emb,
                payload={
                    "session_file": str(path),
                    "project": project,
                    "chunk_text": c["text"],
                    "turns_included": c["turns"],
                    "indexed_at": datetime.utcnow().isoformat(),
                },
            )
            for c, emb in zip(chunks, embeddings)
        ]

        await self.vectors.upsert(self.COLLECTION_NAME, points)

    def _parse_jsonl(self, path: Path) -> list[dict]:
        """Parse JSONL session file."""
        messages = []
        for line in path.read_text().strip().split("\n"):
            if line:
                messages.append(json.loads(line))
        return messages

    def _extract_content(self, msg: dict) -> str | None:
        """Extract text content from message."""
        if isinstance(msg.get("content"), str):
            return msg["content"]
        if isinstance(msg.get("content"), list):
            texts = [
                c.get("text", "")
                for c in msg["content"]
                if c.get("type") == "text"
            ]
            return "\n".join(texts) if texts else None
        return None

    def _chunk_conversation(
        self,
        turns: list[dict],
        max_turns: int = 5,
    ) -> list[dict]:
        """Chunk conversation into overlapping windows."""
        chunks = []
        for i in range(0, len(turns), max_turns - 1):
            window = turns[i:i + max_turns]
            text = "\n\n".join(
                f"{t['role'].upper()}: {t['content']}"
                for t in window
            )
            chunks.append({
                "text": text,
                "turns": len(window),
            })
        return chunks

    async def search(
        self,
        query: str,
        limit: int = 10,
        project: str | None = None,
    ) -> list[dict]:
        """Search sessions by semantic similarity."""
        query_embedding = await self.embedding.embed_single(query)

        filter_ = None
        if project:
            filter_ = Filter(
                must=[FieldCondition(key="project", match=MatchValue(value=project))]
            )

        results = await self.vectors.search(
            collection=self.COLLECTION_NAME,
            vector=query_embedding,
            limit=limit,
            filter_=filter_,
        )

        return [
            {
                "session_file": r["payload"]["session_file"],
                "project": r["payload"]["project"],
                "chunk_text": r["payload"]["chunk_text"],
                "score": r["score"],
            }
            for r in results
        ]
```

---

## Phase 6: Device Management API ❌

**Status:** ❌ NOT STARTED
**Blockers:** None
**Estimated Effort:** 2-3 days

**Implementation Plan:**
- Device service wrapper for ~/memory/bank/ssh/latest.json
- Inventory refresh trigger via homelab/inventory/ssh.sh
- SSH command execution with validation
- synapse-mcp stdio integration via .mcp-server-config.json
- REST endpoints for device listing and operations
- Security validations for command injection prevention

**Goal**: API access to existing device inventory from memory bank + synapse-mcp.

### 6.1 Device Service

```python
# apps/api/services/device_service.py
import asyncio
import json
from pathlib import Path

class DeviceService:
    """Device inventory and execution using existing infrastructure.

    Uses two complementary systems:
    - Memory bank (homelab): Static inventory with temporal snapshots
    - synapse-mcp: Real-time Docker/SSH operations with pooled connections
    """

    INVENTORY_PATH = Path.home() / "memory/bank/ssh/latest.json"
    HOMELAB_PATH = Path.home() / "workspace/homelab"

    async def get_inventory(self) -> list[dict]:
        """Get device inventory from memory bank."""
        if not self.INVENTORY_PATH.exists():
            return []

        data = json.loads(self.INVENTORY_PATH.read_text())
        return data.get("data", {}).get("hosts", [])

    async def get_device(self, name: str) -> dict | None:
        """Get specific device by name."""
        inventory = await self.get_inventory()
        for device in inventory:
            if device.get("hostname") == name:
                return device
        return None

    async def refresh_inventory(self) -> int:
        """Trigger inventory refresh via homelab script."""
        script = self.HOMELAB_PATH / "inventory/ssh.sh"
        proc = await asyncio.create_subprocess_exec(
            "bash", str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError("Inventory refresh timed out after 120 seconds")
        if proc.returncode != 0:
            raise RuntimeError(f"Inventory refresh failed: {stderr.decode()}")

        # Return count of discovered hosts
        inventory = await self.get_inventory()
        return len(inventory)

    async def execute_command(
        self,
        device_name: str,
        command: str,
        timeout: int = 60,
    ) -> dict:
        """Execute command on device via SSH."""
        device = await self.get_device(device_name)
        if not device:
            raise ValueError(f"Device not found: {device_name}")

        if device.get("status") != "reachable":
            raise ValueError(f"Device not reachable: {device_name}")

        # Validate command for dangerous shell metacharacters
        dangerous_chars = [";", "|", "`", "$", "(", ")", "&", "<", ">", "\n", "\r"]
        if any(char in command for char in dangerous_chars):
            raise ValueError(
                f"Command contains dangerous shell metacharacters: {command}"
            )

        # Use homelab remote-exec library
        proc = await asyncio.create_subprocess_exec(
            "ssh",
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=accept-new",
            device["hostname"],
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"Command timed out after {timeout} seconds")

        return {
            "device": device_name,
            "command": command,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "exit_code": proc.returncode,
        }
```

### 6.2 synapse-mcp Integration

**Integration Mode: stdio (MCP protocol)**

We integrate synapse-mcp using stdio mode, NOT HTTP mode. The Claude SDK handles all communication automatically - no custom HTTP client is needed.

**Configuration (.mcp-server-config.json):**

```json
{
  "mcpServers": {
    "synapse": {
      "type": "stdio",
      "command": "node",
      "args": ["../synapse-mcp/dist/index.js"],
      "env": {
        "SYNAPSE_CONFIG_FILE": "../synapse-mcp/synapse.config.json"
      }
    }
  }
}
```

**Usage in queries:**

```python
# No custom client needed - SDK handles all MCP communication

# Query with server-side MCP config (application-level + api-key-level)
response = await sdk_client.query(
    prompt="List all running Docker containers across hosts",
    mcp_servers=None  # Use server-side configs (includes synapse)
)

# The SDK automatically:
# 1. Spawns the synapse MCP server as subprocess
# 2. Calls the flux tool with action="container", subaction="list"
# 3. Pipes stdin/stdout communication
# 4. Returns results in the response
```

**Available Tools (auto-discovered by SDK):**

- **flux**: Docker/Compose operations (40 subactions)
  - Actions: container, compose, system, host
- **scout**: SSH/file/ZFS operations (16 subactions)
  - Actions: nodes, peek, exec, find, delta, emit, beam, ps, df, zfs, logs

**Why stdio mode?**

- **Zero deployment overhead**: SDK auto-starts subprocess on-demand
- **MCP ecosystem compatibility**: Works with all MCP-aware skills and tools
- **Simplified configuration**: Single config file for all MCP servers
- **SDK-managed lifecycle**: No process management code needed

**HTTP mode alternative:**

If you need direct REST API access (e.g., for a web dashboard without Claude SDK), synapse-mcp can run as an independent HTTP server. However, for this assistant, stdio mode via the SDK is the recommended approach.

**When to use which:**

| Use Case | Tool |
|----------|------|
| Static device inventory | Memory bank (`~/memory/bank/ssh/`) |
| Real-time container status | synapse-mcp (Flux tool) |
| Container logs with grep | synapse-mcp (Flux tool) |
| Compose project management | synapse-mcp (Flux tool) |
| ZFS pool health | synapse-mcp (Scout tool) |
| File transfer between hosts | synapse-mcp (Scout tool) |
| System resource monitoring | synapse-mcp (Flux host) |
| Historical infrastructure data | Memory bank (timestamped JSON) |

### 6.3 Device Routes

```python
# apps/api/routes/devices.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/devices", tags=["devices"])

# Memory bank routes (static inventory)

@router.get("")
async def list_devices(
    device_service: DeviceService = Depends(get_device_service),
) -> list[dict]:
    """List all devices from inventory."""
    return await device_service.get_inventory()

@router.get("/{name}")
async def get_device(
    name: str,
    device_service: DeviceService = Depends(get_device_service),
) -> dict:
    """Get device details."""
    device = await device_service.get_device(name)
    if not device:
        raise HTTPException(404, f"Device not found: {name}")
    return device

@router.post("/{name}/exec")
async def execute_command(
    name: str,
    command: str,
    timeout: int = 60,
    device_service: DeviceService = Depends(get_device_service),
) -> dict:
    """Execute command on device (requires confirmation)."""
    return await device_service.execute_command(name, command, timeout)

@router.post("/inventory/refresh")
async def refresh_inventory(
    device_service: DeviceService = Depends(get_device_service),
) -> dict:
    """Refresh SSH inventory."""
    count = await device_service.refresh_inventory()
    return {"hosts_discovered": count}
```

### 6.4 Infrastructure Routes (synapse-mcp)

```python
# apps/api/routes/infrastructure.py
from fastapi import APIRouter, Depends, Query
from apps.api.services.synapse_client import SynapseClient

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])

# Container operations

@router.get("/containers")
async def list_containers(
    host: str = "all",
    state: str | None = None,
    synapse: SynapseClient = Depends(get_synapse_client),
) -> list[dict]:
    """List Docker containers (real-time via synapse-mcp)."""
    return await synapse.list_containers(host=host)

@router.get("/containers/{container}/logs")
async def get_container_logs(
    container: str,
    host: str = "local",
    lines: int = 100,
    grep: str | None = None,
    synapse: SynapseClient = Depends(get_synapse_client),
) -> dict:
    """Get container logs with optional grep filtering."""
    logs = await synapse.container_logs(
        container=container,
        host=host,
        lines=lines,
        grep=grep,
    )
    return {"container": container, "host": host, "logs": logs}

# Compose operations

@router.get("/compose")
async def list_compose_projects(
    host: str = "all",
    synapse: SynapseClient = Depends(get_synapse_client),
) -> list[dict]:
    """List Compose projects (auto-discovered)."""
    return await synapse.flux("compose", "list", host=host)

@router.get("/compose/{project}/status")
async def get_compose_status(
    project: str,
    synapse: SynapseClient = Depends(get_synapse_client),
) -> dict:
    """Get Compose project status (auto-discovers host)."""
    return await synapse.compose_status(project=project)

# Host operations

@router.get("/hosts/{host}/resources")
async def get_host_resources(
    host: str,
    synapse: SynapseClient = Depends(get_synapse_client),
) -> dict:
    """Get CPU/memory/disk usage for a host."""
    return await synapse.host_resources(host=host)

@router.get("/hosts/{host}/zfs/pools")
async def get_zfs_pools(
    host: str,
    synapse: SynapseClient = Depends(get_synapse_client),
) -> list[dict]:
    """Get ZFS pool status and health."""
    return await synapse.zfs_pools(host=host)

@router.get("/hosts/{host}/logs/journal")
async def get_journal_logs(
    host: str,
    unit: str | None = None,
    lines: int = 100,
    priority: str | None = None,
    synapse: SynapseClient = Depends(get_synapse_client),
) -> dict:
    """Get systemd journal logs."""
    logs = await synapse.journal_logs(
        host=host,
        unit=unit,
        lines=lines,
        priority=priority,
    )
    return {"host": host, "unit": unit, "logs": logs}
```

---

## Phase 7: Web App

**Status:** ✅ READY (Architecture Defined)
**Blockers:** None
**Estimated Effort:** 2-3 weeks

**Goal**: Mobile-first PWA for chat, memory management, heartbeat monitoring, and cron job scheduling.

### 7.1 Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Framework** | Next.js 15 | App Router, React Server Components |
| **UI Library** | React 19 | Server Components, Suspense, Transitions |
| **Styling** | TailwindCSS v4 | Utility-first CSS with modern features |
| **Components** | shadcn/ui | Radix UI + Tailwind, accessible primitives |
| **State Management** | React Query + Zustand | Server state + client state |
| **Authentication** | NextAuth.js | API key-based auth with session management |
| **Real-Time** | EventSource (SSE) | Streaming chat responses |
| **Forms** | React Hook Form + Zod | Type-safe validation |
| **Charts** | Recharts | Heartbeat metrics, cron job stats |
| **Notifications** | Sonner | Toast notifications |
| **PWA** | next-pwa | Service worker, offline support |
| **Type Checking** | TypeScript strict | Zero `any` types |
| **Testing** | Jest + Playwright | Unit, integration, E2E |

### 7.2 Architecture Decisions

#### State Management

**Server State (React Query):**
- API data fetching, caching, and synchronization
- Automatic background refetching and stale-while-revalidate
- Optimistic updates for mutations

**Client State (Zustand):**
- UI state (sidebar open/closed, theme, active chat)
- Form state (draft messages, unsaved configs)
- Ephemeral state (loading indicators, modals)

**Session State (NextAuth):**
- API key authentication
- User session persistence
- Automatic token refresh

#### Routing Structure

```tsx
app/
├── (auth)/
│   ├── login/
│   │   └── page.tsx              # API key input
│   └── layout.tsx                # Auth layout (centered, minimal)
├── (dashboard)/
│   ├── layout.tsx                # Main layout (sidebar, header)
│   ├── page.tsx                  # Chat interface (default route)
│   ├── memory/
│   │   ├── page.tsx              # Memory browser
│   │   └── [id]/page.tsx         # Memory detail
│   ├── heartbeat/
│   │   ├── page.tsx              # Dashboard (metrics, history)
│   │   └── settings/page.tsx     # Config (schedule, active hours)
│   ├── cron/
│   │   ├── page.tsx              # Job list
│   │   ├── new/page.tsx          # Create job
│   │   └── [id]/
│   │       ├── page.tsx          # Job detail + runs
│   │       └── edit/page.tsx     # Edit job
│   ├── settings/
│   │   ├── page.tsx              # General settings
│   │   ├── persona/page.tsx      # Persona config
│   │   ├── skills/page.tsx       # Skill management
│   │   └── devices/page.tsx      # Device inventory
│   └── history/
│       ├── page.tsx              # Conversation history
│       └── [sessionId]/page.tsx  # Session detail
├── api/
│   └── auth/
│       └── [...nextauth]/route.ts # NextAuth handler
└── layout.tsx                     # Root layout (providers, fonts)
```

#### Component Architecture

**1. Chat Interface (`/`)**

```tsx
// app/(dashboard)/page.tsx
<ChatLayout>
  <ChatSidebar>                    {/* Collapsible on mobile */}
    <ConversationList />           {/* Recent sessions */}
    <NewChatButton />
  </ChatSidebar>

  <ChatMain>
    <ChatHeader>                   {/* Sticky header */}
      <SessionInfo />
      <ChatActions />              {/* Clear, export, settings */}
    </ChatHeader>

    <MessageList>                  {/* Auto-scroll, virtualized */}
      <MessageBubble />            {/* User/assistant messages */}
      <StreamingMessage />         {/* SSE real-time updates */}
      <MemoryInjectionIndicator /> {/* Show when memories used */}
    </MessageList>

    <ChatInput>                    {/* Fixed bottom */}
      <TextArea />                 {/* Auto-resize, mobile keyboard */}
      <AttachmentButton />         {/* File upload (future) */}
      <SendButton />
    </ChatInput>
  </ChatMain>
</ChatLayout>
```

**2. Memory Management (`/memory`)**

```tsx
// app/(dashboard)/memory/page.tsx
<MemoryLayout>
  <MemoryFilters>
    <SearchBar />                  {/* Semantic search */}
    <FilterByCategory />
    <SortOptions />
  </MemoryFilters>

  <MemoryGrid>
    <MemoryCard>
      <MemoryContent />            {/* Snippet preview */}
      <MemoryMetadata />           {/* Timestamp, category, score */}
      <MemoryActions />            {/* View, edit, delete */}
    </MemoryCard>
  </MemoryGrid>

  <MemoryDetail>                   {/* Sheet/modal on mobile */}
    <MemoryFullContent />
    <RelatedMemories />            {/* Graph relationships */}
    <MemoryHistory />              {/* Edit history */}
  </MemoryDetail>
</MemoryLayout>
```

**3. Heartbeat Dashboard (`/heartbeat`)**

```tsx
// app/(dashboard)/heartbeat/page.tsx
<HeartbeatDashboard>
  <MetricsOverview>
    <StatCard title="Uptime" />
    <StatCard title="Last Run" />
    <StatCard title="Success Rate" />
  </MetricsOverview>

  <ActivityChart>                  {/* Recharts line chart */}
    <TimeSeriesData />             {/* Last 30 days */}
    <InteractiveTooltip />
  </ActivityChart>

  <RecentRuns>
    <RunCard>
      <RunStatus />                {/* Success/failure badge */}
      <RunTimestamp />
      <RunMessage />               {/* Gotify payload */}
    </RunCard>
  </RecentRuns>

  <HeartbeatSettings>              {/* Collapsible panel */}
    <ScheduleEditor />             {/* Cron expression builder */}
    <ActiveHoursToggle />
    <SuppressUntilPicker />
  </HeartbeatSettings>
</HeartbeatDashboard>
```

**4. Cron Job Manager (`/cron`)**

```tsx
// app/(dashboard)/cron/page.tsx
<CronLayout>
  <CronToolbar>
    <NewJobButton />
    <BulkActions />                {/* Enable/disable multiple */}
  </CronToolbar>

  <CronJobList>
    <CronJobCard>
      <JobHeader>
        <JobName />
        <EnabledToggle />
      </JobHeader>
      <JobSchedule />              {/* Human-readable cron */}
      <JobStats>
        <NextRun />
        <LastRun />
        <SuccessRate />
      </JobStats>
      <JobActions />               {/* Edit, run now, delete */}
    </CronJobCard>
  </CronJobList>

  <CronJobDetail>                  {/* Right panel or modal */}
    <JobConfiguration />
    <RunHistory>
      <RunCard>
        <RunOutput />              {/* Agent response */}
        <RunDuration />
        <RunError />               {/* If failed */}
      </RunCard>
    </RunHistory>
  </CronJobDetail>
</CronLayout>
```

#### Authentication Flow

```tsx
// 1. User enters API key on /login
// 2. NextAuth validates key against FastAPI /api/v1/validate-key
// 3. On success, create session with encrypted API key
// 4. Redirect to / (chat interface)
// 5. All API calls use session API key from server-side
// 6. Client never sees raw API key (secure HTTP-only cookie)
// 7. Session expires after 7 days of inactivity
// 8. Auto-logout on API key revocation (detected via 401 response)
```

**Key Hook:**

```tsx
// hooks/useApiKey.ts
export function useApiKey(): string {
  const { data: session } = useSession()
  if (!session?.apiKey) {
    throw new Error('Not authenticated')
  }
  return session.apiKey
}
```

#### Real-Time Updates

**SSE for Chat Streaming:**

```tsx
// hooks/useStreamingChat.ts
import { useEffect, useState } from 'react'

export function useStreamingChat(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (content: string) => {
    setIsStreaming(true)
    const apiKey = await getApiKey()

    const eventSource = new EventSource(
      `/api/v1/query/stream?session_id=${sessionId}&prompt=${encodeURIComponent(content)}`,
      { headers: { 'X-API-Key': apiKey } }
    )

    eventSource.addEventListener('partial', (e) => {
      const data = JSON.parse(e.data)
      setMessages((prev) => appendPartial(prev, data.content))
    })

    eventSource.addEventListener('result', (e) => {
      const data = JSON.parse(e.data)
      setMessages((prev) => finalizeMessage(prev, data))
      setIsStreaming(false)
      eventSource.close()
    })

    eventSource.onerror = () => {
      setIsStreaming(false)
      eventSource.close()
    }
  }

  return { messages, sendMessage, isStreaming }
}
```

**WebSocket for Live Metrics (Future):**

```tsx
// For heartbeat/cron real-time status updates
// Phase 1 uses polling with React Query (refetchInterval: 30000)
// Phase 2 can migrate to WebSocket for sub-second updates
```

### 7.3 Mobile-First Design

**Breakpoints:**

| Breakpoint | Width | Usage |
|------------|-------|-------|
| `xs` | 0-639px | Mobile portrait |
| `sm` | 640-767px | Mobile landscape |
| `md` | 768-1023px | Tablet |
| `lg` | 1024-1279px | Desktop |
| `xl` | 1280+ | Large desktop |

**Mobile Patterns:**

```tsx
// Responsive sidebar (drawer on mobile, fixed on desktop)
<aside className="fixed inset-y-0 left-0 z-50 w-72 bg-background
                   -translate-x-full transition-transform
                   lg:translate-x-0 lg:static">
  {/* Sidebar content */}
</aside>

// Mobile-first chat input
<form className="sticky bottom-0 p-4 bg-background border-t">
  <textarea className="w-full min-h-12 max-h-32 resize-none
                       text-base leading-6 p-3
                       md:text-sm md:leading-5" />
</form>

// Touch-friendly buttons (44px minimum)
<button className="min-h-11 min-w-11 touch-manipulation">
  <Icon className="h-6 w-6" />
</button>
```

**Touch Targets:**
- Minimum 44x44px for all interactive elements
- 8px spacing between adjacent targets
- Larger font sizes on mobile (16px base to prevent zoom)
- Bottom-anchored primary actions (easier thumb reach)

### 7.4 Testing Strategy

**Unit Tests (Jest + React Testing Library):**
- Component rendering and interaction
- Hook behavior (useStreamingChat, useMemories)
- State management (Zustand stores, React Query caching)
- Form validation (Zod schemas)

**Integration Tests (Playwright):**
- API integration (mock FastAPI responses)
- SSE streaming (simulated events)
- Authentication flow (login → chat → logout)
- Offline functionality (service worker interception)

**E2E Tests (Playwright):**
- Critical user journeys (send message, view memories, create cron job)
- Mobile viewport (375x667, 414x896)
- Accessibility (screen reader, keyboard navigation)

**Accessibility Requirements:**
- WCAG 2.1 Level AA compliance
- Semantic HTML (proper heading hierarchy, landmarks)
- ARIA labels for interactive elements
- Keyboard navigation (tab order, focus management)
- Color contrast ≥4.5:1 for text

**Performance Targets:**
- First Contentful Paint (FCP) < 1.5s
- Largest Contentful Paint (LCP) < 2.5s
- Time to Interactive (TTI) < 3.5s
- Cumulative Layout Shift (CLS) < 0.1
- Lighthouse score ≥90 (Performance, Accessibility, Best Practices, SEO)

### 7.5 Progressive Web App

**Service Worker (`public/sw.js`):**
- Cache-first strategy for static assets (JS, CSS, fonts)
- Network-first strategy for API calls
- Offline fallback page for navigation requests
- Background sync for failed message sends

**Web App Manifest (`public/manifest.json`):**

```json
{
  "name": "Agent Orchestration",
  "short_name": "Agent",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "theme_color": "#000000",
  "background_color": "#ffffff",
  "display": "standalone",
  "start_url": "/",
  "scope": "/"
}
```

**Push Notifications (Gotify Integration):**
- Request permission on first message send
- Subscribe to Gotify WebSocket for push events
- Display native notifications for heartbeat alerts
- Badge count for unread messages

### 7.6 Implementation Checklist

**Phase 1: Foundation (Days 1-3)**
- [ ] Project setup (Next.js, TypeScript, Tailwind)
- [ ] NextAuth.js configuration
- [ ] shadcn/ui component installation
- [ ] Layout structure (sidebar, header, main)
- [ ] Dark mode support

**Phase 2: Chat Interface (Days 4-6)**
- [ ] Chat UI (message list, input, sidebar)
- [ ] SSE streaming integration
- [ ] React Query setup for API calls
- [ ] Message history persistence

**Phase 3: Memory Management (Days 7-9)**
- [ ] Memory browser (list, search, filter)
- [ ] Memory detail view (full content, relationships)
- [ ] Memory CRUD operations
- [ ] Graph visualization (optional)

**Phase 4: Heartbeat Dashboard (Days 10-12)**
- [ ] Metrics overview (uptime, success rate)
- [ ] Activity chart (Recharts integration)
- [ ] Run history list
- [ ] Settings editor (schedule, active hours)

**Phase 5: Cron Job Manager (Days 13-15)**
- [ ] Job list (enable/disable, stats)
- [ ] Job creation form (cron builder)
- [ ] Job detail (config, run history)
- [ ] Run now action

**Phase 6: PWA & Polish (Days 16-18)**
- [ ] Service worker setup
- [ ] Offline fallback page
- [ ] Web app manifest
- [ ] Gotify push notifications
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Mobile testing (real devices)

**Estimated Effort:** 2-3 weeks (18 days with 1 developer)

---

## Database Migrations

### Migration 001: Cron Jobs

```sql
-- alembic/versions/xxx_add_cron_tables.py
CREATE TABLE cron_jobs (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    schedule JSONB NOT NULL,
    session_mode VARCHAR DEFAULT 'isolated',
    message TEXT NOT NULL,
    enabled BOOLEAN DEFAULT true,
    deliver BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_count INTEGER DEFAULT 0
);

CREATE TABLE cron_runs (
    id VARCHAR PRIMARY KEY,
    job_id VARCHAR REFERENCES cron_jobs(id),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR NOT NULL,
    output TEXT,
    error TEXT
);

CREATE INDEX idx_cron_jobs_enabled ON cron_jobs(enabled);
CREATE INDEX idx_cron_runs_job_id ON cron_runs(job_id);
```

### Migration 002: Heartbeat History

```sql
-- alembic/versions/xxx_add_heartbeat_history.py
CREATE TABLE heartbeat_runs (
    id VARCHAR PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR NOT NULL,
    delivered BOOLEAN DEFAULT false,
    content TEXT,
    checklist_hash VARCHAR
);

CREATE INDEX idx_heartbeat_runs_started ON heartbeat_runs(started_at);
```

### Migration 003: Persona Config

**Storage implementation:** See [spec.md Persona Endpoints section](spec.md#persona-endpoints-new) for complete database schema, file-based fallback, and decision logic.

```sql
-- alembic/versions/xxx_add_persona_config.py
CREATE TABLE persona_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_api_key_hash VARCHAR(64) NOT NULL,
    name VARCHAR(100) DEFAULT 'Assistant',
    personality TEXT,
    communication_style TEXT,
    expertise_areas JSONB DEFAULT '[]'::jsonb,
    proactivity VARCHAR(20) DEFAULT 'medium',
    verbosity VARCHAR(20) DEFAULT 'balanced',
    formality VARCHAR(20) DEFAULT 'balanced',
    use_emoji BOOLEAN DEFAULT false,
    custom_instructions TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_persona_config_api_key ON persona_config(owner_api_key_hash);

CREATE TRIGGER update_persona_config_updated_at
    BEFORE UPDATE ON persona_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Note:** PostgreSQL is the primary storage mechanism with API key scoping. JSON file (`~/.config/assistant/persona.json`) is fallback for single-user deployments when `DATABASE_URL` is not configured.

---

## Testing Strategy

### Unit Tests

- Memory service (add, search, context injection)
- Embedding service (TEI client)
- Vector service (Qdrant client)
- Heartbeat scheduler (active hours, suppression)
- Cron executor (scheduling, session modes)
- QMD service (chunking, indexing)
- Session search (parsing, indexing)
- Device service (inventory reading)

### Integration Tests

- Memory search with real TEI + Qdrant
- Heartbeat execution with Gotify
- Cron job lifecycle
- QMD indexing and search
- Session search
- Device command execution

### Coverage Target

- Unit tests: ≥90%
- Integration tests: ≥80%
- Overall: ≥85%

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Deployment complexity | Single `docker compose up` |
| TEI + Qdrant integration | Zero additional setup (use existing) |
| Memory search latency | < 200ms |
| Heartbeat success rate | 99.9% |
| Skill compatibility | 100% AgentSkills spec |
| Code reuse | 100% of cli-firecrawl and homelab |
| OpenClaw feature coverage | ~90% |

---

## Next Steps

**Priority Order:**

1. **Phase 2: Heartbeat System** (Ready to start)
   - No blockers, depends only on completed Phase 1
   - 5-7 days estimated effort
   - Provides immediate value with proactive monitoring

2. **Phase 3: Cron Jobs** (Ready to start)
   - No blockers, depends only on completed Phase 1
   - 4-6 days estimated effort
   - Can be developed in parallel with Phase 2

3. **Phase 6: Device Management API** (Ready to start)
   - No blockers, standalone implementation
   - 2-3 days estimated effort
   - Quick win, leverages existing homelab infrastructure

4. **Unblock Phase 4 & 5** (Memory system decisions)
   - Finalize Mem0 integration patterns
   - Decide on collection isolation strategy
   - Determine if Mem0 can handle QMD/session indexing natively

5. **Phase 7: Web App** (Architectural decisions)
   - Resolve framework and tooling choices
   - Finalize API contract
   - Can begin once Phases 2-3 are complete

**Critical Path:**
Phase 1 (✅) → Phase 2 (5-7d) → Phase 3 (4-6d) → Phase 4 (3-5d) → Phase 5 (4-6d) → Phase 6 (2-3d) → Phase 7 (2-3w)

**Optimization:**
Phases 2, 3, and 6 can be developed in parallel since they have no interdependencies. This could reduce the overall timeline from ~30 days to ~15 days if multiple developers are available.

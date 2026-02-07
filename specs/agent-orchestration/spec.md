# Personal AI Assistant Specification

## Vision

A simplified, Claude-only personal AI assistant inspired by OpenClaw's capabilities but with dramatically reduced complexity. We achieve ~90% of OpenClaw's functionality with ~10% of the architectural complexity by:

1. **Claude-only**: No multi-model support. Claude MAX subscription or API key only.
2. **Web-first**: Mobile-first PWA instead of WhatsApp/Telegram/Discord/Slack/iMessage integrations.
3. **Unified codebase**: FastAPI + Next.js instead of Gateway/Control UI/Daemon/Node architecture.
4. **Skills-compatible**: Full AgentSkills spec support for ecosystem compatibility.
5. **SSH-based device access**: Simple key-based SSH instead of complex multi-node orchestration.

## Existing Infrastructure

### What Already Exists

#### claude-agent-api (This Repository)

✅ **Full Skills System** - Filesystem + database skill discovery, CRUD API, auto-injection into queries
✅ **FastAPI Backend** - Async routes, SSE streaming, OpenAI compatibility layer
✅ **Three-Tier MCP Config** - Application → API-Key → Request level MCP server injection
✅ **Session Storage** - Redis cache + PostgreSQL durability
✅ **Type-Safe Schemas** - Pydantic models with zero `Any` types
✅ **Claude Code SDK** - Full tool access (bash, filesystem, git, etc.)

#### cli-firecrawl (`../cli-firecrawl`)

✅ **Firecrawl Integration** - Web scraping CLI with 13 commands (scrape, crawl, map, search, extract, etc.)
✅ **TEI Integration** - Text Embeddings Inference at `http://localhost:52000` for vector generation
✅ **Qdrant Integration** - Vector database at `http://localhost:53333` with semantic search
✅ **Embedding Pipeline** - Automatic chunking → embedding → storage workflow
✅ **Semantic Search** - `firecrawl query <text>` for vector similarity search

#### homelab (`../homelab`)

✅ **13+ Domain Skills** - tailscale, unifi, unraid, radarr, sonarr, prowlarr, sabnzbd, qbittorrent, plex, overseerr, gotify, glances, linkding
✅ **SSH Inventory Discovery** - Parses `~/.ssh/config` to build device inventory
✅ **Remote Execution** - Timeout-protected SSH with parallel support
✅ **Memory Bank Integration** - Writes to `~/memory/bank/` with temporal JSON snapshots
✅ **Gotify Notifications** - Push notifications via self-hosted Gotify server
✅ **Infrastructure Monitoring** - Dashboard scripts for Unraid, Linux, UniFi

#### Memory Bank (`~/memory/bank/`)

✅ **Temporal Data Storage** - Timestamped JSON snapshots per topic
✅ **Human-Readable Dashboards** - `latest.md` markdown summaries
✅ **12 Topic Directories** - docker, linux, unraid, unifi, tailscale, ssh, swag, overseerr, weekly
✅ **Device Inventory** - 9 SSH hosts, 144 Docker containers, 2 Unraid servers, 33 network clients

#### synapse-mcp (`../synapse-mcp`)

✅ **Infrastructure MCP Server** - Unified multi-host Docker + SSH management via MCP protocol
✅ **Flux Tool (40 operations)** - Container lifecycle, Compose management, system operations, host resources
✅ **Scout Tool (16 operations)** - SSH commands, file transfer, ZFS pools, log retrieval (syslog, journal, dmesg)
✅ **Auto-Discovery** - Reads `~/.ssh/config`, auto-discovers Compose projects across hosts
✅ **Connection Pooling** - 50× performance improvement for repeated SSH operations
✅ **Security Hardened** - Command allowlists, path traversal prevention, SSH injection protection
✅ **Multi-Host Transparent** - Seamless operations across all configured SSH hosts

#### Chrome Integration (Claude Code Built-in)

✅ **Browser Automation** - Navigate, click, type, fill forms, scroll via Claude in Chrome extension
✅ **Live Debugging** - Read console errors/logs, DOM state directly from browser
✅ **Authenticated Apps** - Access Google Docs, Gmail, Notion without API setup (uses existing login)
✅ **Data Extraction** - Pull structured info from web pages, save locally
✅ **Task Automation** - Form filling, multi-site workflows, data entry
✅ **Session Recording** - Record browser interactions as GIFs
✅ **Web App Testing** - Test forms, verify user flows, check visual regressions

**Setup**: `claude --chrome` or `/chrome` command in session

**Key Use Cases**:
- Test our web app during development
- Browse ClawHub to discover/evaluate skills
- Interact with authenticated services (Google, Notion, etc.) without API connectors
- Extract data from web pages
- Automate repetitive browser tasks

#### LLM Gateway (Multi-Provider Support)

✅ **Environment Variable Config** - Switch providers via `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`
✅ **Model Aliases** - `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`
✅ **Subagent Models** - `CLAUDE_CODE_SUBAGENT_MODEL` for fast agent tasks
✅ **Multiple Providers** - DeepSeek, z.ai/GLM, Kimi/Moonshot, OpenRouter (via y-router)

**Supported Providers**:
| Provider | Base URL | Notes |
|----------|----------|-------|
| Anthropic | (default) | Claude models, MAX subscription |
| DeepSeek | `https://api.deepseek.com` | Cost-effective coding |
| Kimi/Moonshot | `https://api.moonshot.ai/anthropic` | 128K+ context |
| OpenRouter | `http://localhost:8787` (via y-router) | 100+ models |

**Our Strategy**:
- **Default**: Claude (MAX subscription) - primary
- **Cost Optimization**: DeepSeek/Haiku for bulk operations, background tasks
- **Subagents**: Haiku model for fast, cheap parallel agent execution

## Core Features (from OpenClaw)

### 1. Persistent Memory & Persona

**What OpenClaw does:**
- Learns user patterns over time
- Maintains context across sessions
- Customizable personality ("soul")
- Remembers relationships, preferences, workflows

**Our implementation:**
- **Mem0 OSS Integration**: Graph-enhanced memory with automatic entity extraction
- **Multi-Component Architecture**:
  - LLM: Gemini 3 Flash Preview (cli-api.tootie.tv) for memory extraction
  - Embeddings: Qwen/Qwen3-Embedding-0.6B (1024-dim) via TEI at 100.74.16.82:52000
  - Vector Store: Qdrant (localhost:53333) for semantic search
  - Graph Store: Neo4j (localhost:54687) for relationships and entities
  - History: SQLite (~/.mem0/history.db) for operation tracking
- Memory bank (`~/memory/bank/`) for structured data snapshots
- Persona configuration via YAML/JSON

**Mem0 Architecture:**

```
Request →
  mem0.search(user_id=api_key) → inject memories →
  Claude response →
  mem0.add(conversation, user_id=api_key)
```

**Memory Schema:**

```python
class Memory:
    id: str
    memory: str  # Memory content (text)
    user_id: str  # API key for tenant isolation
    agent_id: str  # Agent identifier (e.g., "main")
    metadata: dict[str, str | int | float | bool]  # Custom metadata
    created_at: datetime
    updated_at: datetime
```

**Embedding Storage:**
- **Dimensionality**: 1024 dimensions (Qwen/Qwen3-Embedding-0.6B)
- **Storage Strategy**: Dual storage with graph enhancement
  - **Qdrant**: Vector embeddings for semantic search (1024 floats × 4 bytes = 4KB per embedding)
  - **Neo4j**: Entity/relationship graph for contextual connections
  - **SQLite**: Operation history and metadata (~/.mem0/history.db)
  - 10K memories ≈ 40MB in Qdrant + graph relationships in Neo4j
- **Compression**: Qdrant supports scalar/product quantization (8x reduction)
- **Vector Search**: Sub-100ms for 1M+ vectors with HNSW indexing

**Graph Memory Features:**
- **Automatic Entity Extraction**: Mem0 extracts entities (people, places, things) and relationships from conversations using the configured LLM
- **Dual Retrieval**: Vector similarity search returns semantically related memories plus graph-connected entities
- **Contextual Enrichment**: Graph relationships provide additional context beyond vector similarity
- **Performance Trade-off**: Graph operations add ~100-200ms latency per request
- **Per-Request Toggle**: Disable graph with `enable_graph=False` for high-frequency operations

**Graph Memory Example:**

```python
# User conversation: "I met Sarah at the Anthropic office in San Francisco"
# Mem0 automatically extracts:
# - Entities: Sarah (person), Anthropic (company), San Francisco (location)
# - Relationships: "met_at" → links Sarah to Anthropic office
#                  "located_in" → links office to San Francisco

# Future query: "Where does Sarah work?"
# Vector search finds: "met Sarah at Anthropic office"
# Graph context adds: "Anthropic office located in San Francisco"
# Combined result provides richer answer
```

**Memory Security & Privacy:**

1. **Encryption at Rest:**
   - Qdrant: Disk encryption via LUKS/dm-crypt at OS level
   - Neo4j: Disk-level encryption (LUKS/dm-crypt) or Neo4j Enterprise TDE
   - SQLite: File-level encryption via SQLCipher (optional)
   - Embedding vectors and graph data encrypted at storage layer

2. **Data Retention & Garbage Collection:**
   - Mem0 provides custom GC via API (no built-in TTL):
     ```python
     # Query, filter, and delete pattern
     old_memories = memory.get_all(
         user_id=api_key,
         filters={"created_at": {"$lt": cutoff_date}}
     )
     for m in old_memories:
         memory.delete(m["id"])
     ```
   - Deletion cascades across all stores (Qdrant + Neo4j + SQLite)
   - Configurable retention policies per memory category (use metadata filters)

3. **Access Control:**
   - All memory operations scoped to `user_id` (mapped from API key)
   - **Multi-Tenant Isolation**:
     - Qdrant: Payload filters on user_id/agent_id at query time
     - Neo4j: Entity/relationship nodes tagged with ownership metadata
     - SQLite: Per-user filtering on all operations
   - No cross-contamination: API keys cannot access other tenants' memories
   - Agent scoping: Optional `agent_id` for multi-agent isolation within tenant

4. **PII Detection & Handling:**
   - Pre-storage PII scan using regex patterns (SSN, credit card, email, phone)
   - Flagged memories: Store PII flags in metadata: `{"contains_pii": true, "pii_types": ["email", "phone"]}`
   - Redaction workflow:
     - Automatic: Replace detected PII with placeholders (`[EMAIL]`, `[PHONE]`)
     - Manual review: Flag for user confirmation before storage
   - Configurable PII handling mode: `block`, `redact`, `flag`, `allow`

5. **Audit Logging:**
   - Mem0's SQLite history database tracks all operations:
     - `~/.mem0/history.db` contains: user_id, memory_id, operation (add/search/delete), timestamp
   - Additional audit table in PostgreSQL for API-level tracking:
     - `memory_audit` table: api_key, memory_id, operation, timestamp, ip_address
   - Retention: 90 days for compliance, then archived/deleted
   - Query patterns for anomaly detection (excessive access, bulk exports)

**Mem0 OSS vs Custom Implementation:**

We chose Mem0 OSS over building a custom memory system. Here's why:

| Aspect | Custom Implementation | Mem0 OSS |
|--------|----------------------|----------|
| **Vector search** | Qdrant client code (100+ lines) | Built-in, 1 config block |
| **Graph memory** | Custom Neo4j entity extraction (500+ lines) | Automatic extraction with LLM |
| **Multi-tenant** | Manual user_id filtering per query | Built-in scoping via `user_id` |
| **LLM extraction** | Custom prompts + parsing logic (200+ lines) | Configurable LLM provider |
| **Maintenance** | Update breaking changes in 3+ libraries | Single `pip install mem0ai` upgrade |
| **Time to implement** | 2-3 weeks (vector + graph + multi-tenant) | 1 day (configuration only) |

**Why we chose Mem0:**

Mem0 provides:
- **Proven entity extraction**: Production-tested LLM prompts for extracting entities and relationships
- **Dual storage orchestration**: Automatic sync between Qdrant (vectors) and Neo4j (graph)
- **Multi-store abstraction**: Single API for vector search + graph retrieval
- **Configurable stack**: Swap LLM/embedder/vector store without code changes
- **Community support**: Active development, bug fixes, new features

**Trade-offs:**

- **Extra dependency**: Adds `mem0ai` package (~5MB)
- **LLM cost for extraction**: Entity extraction requires LLM API calls (mitigated by using cheap Gemini 3 Flash)
- **Opinionated schema**: Memory format is Mem0's, not fully custom

**Decision:** Mem0's time savings (2-3 weeks → 1 day) and maintenance reduction justify the trade-offs. We gain production-grade memory with minimal implementation effort.

**Mem0 Configuration:**

Complete configuration example using our multi-component stack:

```python
from mem0 import Memory
import os

config = {
    # LLM Provider (for memory extraction)
    "llm": {
        "provider": "openai",
        "config": {
            "base_url": "https://cli-api.tootie.tv/v1",
            "model": "gemini-3-flash-preview",
            "api_key": os.environ.get("LLM_API_KEY", "")
        }
    },

    # Embedder (TEI on remote host - Qwen/Qwen3-Embedding-0.6B)
    "embedder": {
        "provider": "openai",  # TEI exposes OpenAI-compatible API
        "config": {
            "model": "text-embedding-3-small",  # Dummy model name (TEI ignores this)
            "openai_base_url": "http://100.74.16.82:52000/v1",
            "embedding_dims": 1024,  # Qwen/Qwen3-Embedding-0.6B output dimension
            "api_key": "not-needed"  # TEI doesn't require auth
        }
    },

    # Vector Store (Qdrant)
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 53333,
            "collection_name": "mem0_memories",
            "embedding_model_dims": 1024,  # Must match embedder
            "distance": "cosine",
            "on_disk": True
        }
    },

    # Graph Store (Neo4j)
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:54687",
            "username": "neo4j",
            "password": "neo4jpassword",
            "database": "neo4j"
        }
    },

    "version": "v1.1"
}

# Initialize memory service
memory = Memory.from_config(config)

# Usage example
memory.add(
    messages="User prefers technical explanations",
    user_id=api_key,  # Tenant isolation
    agent_id="main",
    metadata={"category": "preferences"}
)

results = memory.search(
    query="What are the user's preferences?",
    user_id=api_key,  # Scoped to tenant
    agent_id="main"
)
```

**Environment Variables:**

```bash
# LLM for entity extraction
LLM_API_KEY=<cli-api-key>

# External services (already configured)
QDRANT_URL=http://localhost:53333
TEI_URL=http://100.74.16.82:52000
NEO4J_URL=bolt://localhost:54687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4jpassword
```

**Mem0 Performance Tuning:**

Graph operations add latency (~50ms vector-only vs ~200ms with graph). Use the `enable_graph` parameter to control behavior:

**Disable graph for high-frequency operations:**

```python
# Fast: Vector search only (~50ms)
memory.add(
    messages="System heartbeat at 2026-02-06 14:30",
    user_id=api_key,
    enable_graph=False  # Skip entity extraction
)

results = memory.search(
    query="Recent system activity",
    user_id=api_key,
    enable_graph=False  # Skip graph retrieval
)
```

**Enable graph for context-rich queries:**

```python
# Slower but richer: Vector + graph (~200ms)
memory.add(
    messages="User met Sarah at the Anthropic office in San Francisco",
    user_id=api_key,
    enable_graph=True  # Extract entities (Sarah, Anthropic, San Francisco)
)

results = memory.search(
    query="Where does Sarah work?",
    user_id=api_key,
    enable_graph=True  # Include graph relationships
)
```

**When to disable graph:**

- Heartbeat checks (routine status, no relationships)
- Real-time chat (low latency priority)
- Batch operations (thousands of memories)
- Simple fact storage (no entities to extract)

**When to enable graph:**

- Complex queries requiring context ("Who does X work with?")
- Relationship-heavy conversations (people, places, companies)
- User questions about past interactions
- Building knowledge graphs from conversations

**Latency impact:**

- **Vector-only** (`enable_graph=False`): ~50ms per operation
- **Vector + graph** (`enable_graph=True`): ~200ms per operation (4x slower)

Default: `enable_graph=True` for maximum context. Override per-request for performance.

### 2. AgentSkills-Compatible Skills System

**Current State: ✅ ALREADY IMPLEMENTED**

The claude-agent-api already has a complete skill system:

- **Routes**: `/api/v1/skills` with full CRUD operations
- **Sources**: Filesystem (`~/.claude/skills/*.md`) + Database (Redis)
- **Discovery**: `SkillsService` discovers skills from global and project paths
- **Persistence**: `SkillCrudService` stores API-created skills in Redis
- **Injection**: `QueryEnrichmentService` auto-injects skills into queries
- **Built-in Tools**: "Skill" is in `BUILT_IN_TOOLS` constant

**What we add:**
- Hot-reload via file watcher
- Skill gating enforcement (check env vars, binaries, config)
- Integration with homelab skills

### 3. Heartbeat (Proactive Awareness)

**What OpenClaw does:**
- Periodic agent runs (default 30 min)
- Batches multiple checks in one turn (inbox, calendar, notifications)
- Context-aware prioritization
- Smart suppression (HEARTBEAT_OK if nothing important)
- Active hours configuration
- HEARTBEAT.md checklist

**Our implementation:**
- Background scheduler (APScheduler with PostgreSQL persistence)
- Configurable heartbeat interval
- HEARTBEAT.md in user workspace
- Active hours support
- **Gotify push notifications** (existing homelab integration)
- Heartbeat history logging
- **gog skill** for Gmail/Calendar checks (clawhub.com)

**APScheduler Persistence & Reliability:**

1. **Job Persistence:**
   - PostgreSQLJobStore for durable job storage
   - Survives application restarts (jobs auto-resume)
   - Job state includes: next_run_time, misfire_grace_time, coalesce settings

2. **Missed Heartbeat Recovery:**
   - `misfire_grace_time`: 5 minutes (if heartbeat missed by <5min, still execute)
   - `coalesce=True`: Multiple missed runs coalesce into one execution
   - Prevents backlog of queued heartbeats after downtime

3. **Backpressure Handling:**
   - `max_instances=1`: Only one heartbeat runs at a time (prevents overlap)
   - `replace_existing=True`: New config overwrites old job definition
   - Rate limiting: Minimum 5-minute interval enforced

4. **Failsafe Limits:**
   - Backoff after 3 consecutive failures: exponential backoff (5min → 10min → 20min)
   - Bounded catch-up: After >24h downtime, skip missed runs (configurable)
   - Alert user via Gotify if heartbeat fails 5+ times consecutively

5. **Configuration Knobs:**
   ```python
   class HeartbeatPersistenceConfig:
       heartbeat_interval: int = 30  # minutes
       misfire_grace_time: int = 300  # seconds (5 min)
       max_instances: int = 1
       coalesce: bool = True
       max_consecutive_failures: int = 5
       max_backfill_hours: int = 24  # Skip runs older than this
       backoff_multiplier: float = 2.0  # Exponential backoff
   ```

**Heartbeat Checks via gog (Google):**

```bash
# Check urgent emails
gog gmail search 'newer_than:30m is:unread' --max 5 --json

# Upcoming calendar events
gog calendar events primary --from now --to +2h --json

# Drive activity
gog drive search 'modifiedTime > 1d' --max 10 --json
```

**Heartbeat Checks via caldav (iCloud/Fastmail/Nextcloud):**

```bash
# Sync first
vdirsyncer sync

# Upcoming events
khal list today 7d --format "{start-date} {start-time} {title}"

# Search events
khal search "meeting"
```

```python
class HeartbeatConfig:
    enabled: bool = True
    interval_minutes: int = 30
    active_hours: tuple[str, str] = ("08:00", "22:00")
    timezone: str | None = None  # None = system timezone, or IANA timezone string
    checklist_path: str = "~/.config/assistant/HEARTBEAT.md"
    notification_method: Literal["gotify", "none"] = "gotify"
```

**Timezone Handling:**

The `timezone` field is user-configurable and defaults to the system timezone:

```python
from zoneinfo import ZoneInfo, available_timezones
import time

def get_heartbeat_timezone(config: HeartbeatConfig) -> ZoneInfo:
    """
    Get the timezone for heartbeat scheduling.

    Args:
        config: Heartbeat configuration with optional timezone

    Returns:
        ZoneInfo instance for the configured timezone

    Raises:
        ValueError: If timezone string is invalid
    """
    if config.timezone is None:
        # Use system timezone (POSIX localtime)
        if hasattr(time, 'tzname') and time.tzname[0]:
            # Try to detect system timezone (best effort)
            # Fall back to UTC if detection fails
            try:
                return ZoneInfo('UTC')  # Safe default
            except Exception:
                return ZoneInfo('UTC')
        return ZoneInfo('UTC')

    # Validate user-provided timezone
    if config.timezone not in available_timezones():
        raise ValueError(
            f"Invalid timezone: {config.timezone}. "
            f"Must be a valid IANA timezone string (e.g., 'America/New_York', 'Europe/London')."
        )

    return ZoneInfo(config.timezone)
```

**Usage in Scheduler:**
```python
# APScheduler configuration
tz = get_heartbeat_timezone(config)
scheduler.add_job(
    heartbeat_check,
    trigger=IntervalTrigger(minutes=config.interval_minutes, timezone=tz),
    id='heartbeat',
    replace_existing=True,
)
```

### Heartbeat Session Management

**Session mode options:**

The heartbeat system supports two session modes:

1. **Main session mode** (`session_mode: "main"`)
2. **Isolated session mode** (`session_mode: "isolated"`)

**Main session behavior:**

- Uses a single persistent session (`session_id="heartbeat-main"`)
- Context accumulates across all heartbeat executions
- Enables learning from previous checks and alerts
- Automatically resets after 50 conversation turns to prevent unbounded context growth
- Best for: Situations where historical context improves decision-making

**Isolated session behavior:**

- Creates a fresh session for each heartbeat execution
- No context carryover between runs
- Prevents unbounded memory growth
- Session is destroyed immediately after completion
- Best for: Independent status checks without needing historical context

**Default: `isolated`**

The default session mode is `isolated` to prevent unbounded context growth in long-running deployments. This ensures predictable memory usage and prevents the main session from accumulating excessive history.

**Configuration:**

```python
class HeartbeatConfig:
    enabled: bool = True
    interval_minutes: int = 30
    session_mode: Literal["main", "isolated"] = "isolated"  # Session mode
    active_hours: tuple[str, str] = ("08:00", "22:00")
    timezone: str | None = None
    checklist_path: str = "~/.config/assistant/HEARTBEAT.md"
    notification_method: Literal["gotify", "none"] = "gotify"
```

**Session lifecycle (isolated mode):**

```python
async def _execute_heartbeat(self) -> HeartbeatResult:
    """Execute heartbeat check with isolated session."""
    # 1. Create fresh session
    session_id = f"heartbeat-{uuid4()}"

    # 2. Inject relevant memories (optional)
    memories = await self.memory.search(
        query="system status and alerts",
        user_id=self.api_key,
        limit=5
    )
    memory_context = "\n".join([m["memory"] for m in memories])

    # 3. Execute query with memory context
    prompt = f"""
{memory_context}

Time for your periodic check-in. Review this checklist:

{checklist}

If nothing needs attention, respond with: HEARTBEAT_OK
Otherwise, summarize what needs my attention.
"""

    response = await self.query.execute(
        QueryRequest(prompt=prompt, session_id=session_id)
    )

    # 4. Extract new memories from response (optional)
    await self.memory.add(
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response.content}
        ],
        user_id=self.api_key
    )

    # 5. Send notification if needed
    if "HEARTBEAT_OK" not in response.content:
        await self.gotify.send(
            title="🫀 Heartbeat Alert",
            message=response.content[:500],
            priority=7
        )

    # 6. Session is automatically destroyed (isolated mode)
    # No explicit cleanup needed - SDK handles session lifecycle

    return HeartbeatResult(...)
```

**Main session turn limit:**

When using `session_mode="main"`, the heartbeat service automatically resets the main session after 50 conversation turns to prevent unbounded context growth. This ensures long-running heartbeat deployments don't accumulate excessive history while still maintaining useful short-term context.

```python
# Automatic reset logic (main session mode)
turn_count = await self.session.get_turn_count("heartbeat-main")
if turn_count >= 50:
    await self.session.reset("heartbeat-main")
    logger.info("Reset heartbeat-main session (50 turn limit)")
```

### 4. Cron Jobs (Scheduled Tasks)

**What OpenClaw does:**
- Precise timing with cron expressions
- One-shot reminders with `--at`
- Main session (shared context) vs isolated session (fresh)
- Delivery to channels
- Model overrides per job
- Job persistence and history

**Our implementation:**
- APScheduler with cron triggers
- PostgreSQL job storage
- Main vs isolated session modes
- **Gotify notifications** for delivery (existing homelab integration)
- Job CRUD API endpoints
- Execution history with status

```python
class CronJob:
    id: str
    name: str
    schedule: CronSchedule | AtSchedule | EverySchedule
    session_mode: Literal["main", "isolated"]
    payload: SystemEvent | AgentTurn
    enabled: bool = True
    created_at: datetime
    last_run: datetime | None
    next_run: datetime | None

# Supporting types referenced in CronJob.payload

class SystemEvent:
    """System-generated event (e.g., heartbeat trigger, scheduled check)"""
    event_type: Literal["heartbeat", "scheduled_check", "reminder", "alert"]
    source: str  # e.g., "heartbeat_scheduler", "cron_job_123"
    metadata: dict[str, str | int | float | bool]  # Event-specific data
    timestamp: datetime

class AgentTurn:
    """Agent execution turn (prompt + context for isolated session)"""
    agent_id: str  # Agent identifier for tracking
    inputs: dict[str, str]  # Input context (e.g., {"prompt": "Check emails"})
    outputs: dict[str, str] | None  # Execution results (populated after run)
    status: Literal["pending", "running", "completed", "failed"]
    timestamp: datetime
    error_message: str | None  # If status == "failed"
```

### 5. Full System Access

**What OpenClaw does:**
- Runs on dedicated computer
- Can write code, execute scripts, modify files
- Access to all local tools and APIs

**Our implementation:**
- Claude Code SDK provides full tool access
- Bash, filesystem, git, etc. via SDK
- Configurable tool permissions
- Audit logging for all tool calls

### 6. Device Management (SSH)

**Current State: ✅ ALREADY IMPLEMENTED (via homelab)**

The homelab project already provides:

- **SSH Inventory Discovery** (`inventory/ssh.sh`):
  - Parses `~/.ssh/config` to extract hosts
  - Detects OS type (Linux, Darwin, Unraid)
  - Tracks capabilities (docker, systemd, etc.)
  - Stores in `~/memory/bank/ssh/latest.json`

- **Remote Execution** (`lib/remote-exec.sh`):
  - Timeout protection (connect: 10s, command: 60s)
  - Parallel SSH support (max 3 concurrent)
  - Script deployment with hash-based updates

**What we add:**
- API endpoints to query device inventory
- Integration with skill system for device control
- Real-time device status via existing monitoring

**Current inventory:**
- 9 SSH hosts (6 reachable, 3 unreachable)
- Hosts: clawd, shart, squirts, steamy-wsl, tootie, vivobook-wsl
- Capabilities tracked per host

#### Device Management: Memory Bank vs synapse-mcp

Memory bank and synapse-mcp are **complementary tools** that serve different purposes in device management:

**Decision Matrix:**

| Use Case | Tool | Reason |
|----------|------|--------|
| Static device inventory | Memory bank | Historical snapshots, device capabilities, OS types |
| Device capabilities lookup | Memory bank | Pre-indexed metadata (docker, systemd, etc.) |
| Real-time container status | synapse-mcp Flux | Live Docker API queries across hosts |
| Container logs with grep | synapse-mcp Flux | Stream logs with filtering |
| Compose project management | synapse-mcp Flux | Up/down/restart/build operations |
| ZFS pool health | synapse-mcp Scout | Real-time pool status and dataset info |
| File transfers | synapse-mcp Scout | Beam tool for host-to-host transfers |
| System resource monitoring | synapse-mcp Flux | Live CPU/memory/disk stats |
| Command execution | synapse-mcp Scout | Allowlisted commands with safety |
| Historical trends | Memory bank | Timestamped snapshots for trend analysis |

**Rule of thumb:**

- **Memory bank**: "What devices exist and what are their capabilities?"
- **synapse-mcp**: "What is the current state and can you change it?"

**Example workflow combining both tools:**

1. Query memory bank: "Which hosts have Docker installed?"
2. Use synapse-mcp Flux: "Get real-time container status on those hosts"
3. Use synapse-mcp Scout: "Check ZFS pool health on storage hosts"
4. Write to memory bank: "Update inventory snapshot with findings"

### 7. MCP Server Integration

**Current State: ✅ ALREADY IMPLEMENTED**

- Three-tier MCP config (Application → API-Key → Request)
- Skills can reference MCP tools
- Security validation (command injection, SSRF prevention)

**synapse-mcp Integration:**

The synapse-mcp server provides unified infrastructure management:

```json
// .mcp-server-config.json
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

**Available Operations:**

| Tool | Action | Subactions |
|------|--------|------------|
| Flux | container | list, start, stop, restart, logs, stats, inspect, exec, pull, recreate |
| Flux | compose | list, status, up, down, restart, logs, build, pull |
| Flux | system | info, df, prune, images, networks, volumes |
| Flux | host | status, resources, info, uptime, services, network, mounts |
| Scout | - | nodes, peek, exec, find, delta, emit, beam, ps, df |
| Scout | zfs | pools, datasets, snapshots |
| Scout | logs | syslog, journal, dmesg, auth |

**Use Cases:**
- Check container status across all hosts
- View logs from any service
- Transfer files between hosts
- Query ZFS pool health
- Monitor system resources
- Execute commands with allowlist protection

**Integration Approach:**

synapse-mcp supports two integration modes:

1. **stdio mode (MCP protocol)** - Recommended
   - Run as subprocess managed by Claude SDK
   - Auto-starts on first MCP tool invocation
   - Configured via `.mcp-server-config.json`
   - SDK handles all communication automatically
   - No custom HTTP client needed

2. **HTTP mode (REST API)** - Alternative
   - Run as independent server process
   - Direct REST calls for infrastructure queries
   - Separate deployment/lifecycle management
   - Better for multi-user or web dashboard scenarios

**Our choice: stdio mode**

We use stdio mode because:
- **Zero deployment overhead**: No separate server to manage, SDK auto-starts the subprocess
- **MCP ecosystem compatibility**: Works seamlessly with all MCP-aware tools and skills
- **Simplified configuration**: Single `.mcp-server-config.json` file for all MCP servers
- **SDK-managed lifecycle**: Claude SDK handles process spawning, stdin/stdout piping, and cleanup

**HTTP mode use case:**

HTTP mode is useful when:
- Building a web dashboard that queries infrastructure without Claude SDK
- Supporting multiple concurrent users with persistent connection pooling
- Integrating with non-MCP tools or legacy systems requiring REST APIs

For our personal assistant, stdio mode provides the simplest integration path.

### 8. Semantic Search (QMD - Query Markup Documents)

**New Feature**

On-device semantic search for markdown files:
- Leverages existing TEI + Qdrant infrastructure
- Index markdown files from configurable directories
- Semantic search across documentation, notes, project files

**Implementation:**

- **Skill**: QMD skill for searching markdown files
- **Hook**: Auto-index new/modified markdown files
- **Integration**: Use cli-firecrawl's embed pipeline

```python
class QMDConfig:
    watch_directories: list[str] = [
        "~/Documents",
        "~/workspace",
        "~/notes",
    ]
    exclude_patterns: list[str] = [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
    ]
    collection_name: str = "qmd_documents"
```

### 9. Session Search & Retrieval

**New Feature**

Semantic search across Claude session logs:
- Index sessions from `~/.claude/projects/*/`
- Search past conversations by topic
- Retrieve relevant context from historical sessions

**Implementation:**

- Parse JSONL session files
- Extract user prompts and assistant responses
- Generate embeddings via TEI
- Store in Qdrant with session metadata

```python
class SessionSearchConfig:
    session_root: str = "~/.claude/projects"
    collection_name: str = "claude_sessions"
    include_tool_calls: bool = False
    max_sessions: int | None = None  # None = all
    exclude_paths: list[str] = []  # Paths to exclude from indexing
    redact_patterns: list[str] = []  # Regex patterns for redaction
    require_consent: bool = True  # Require explicit consent for session indexing
    retention_days: int | None = None  # None = infinite retention
```

**Privacy & Sanitization:**

Session data may contain sensitive information (API keys, tokens, passwords, PII). The `sanitize_session_text()` routine runs **before** embedding generation and vector storage to protect user privacy:

**Sanitization Routine:**
```python
import re

def sanitize_session_text(text: str, redact_patterns: list[str]) -> tuple[str, bool]:
    """
    Sanitize session text before embedding/storage.

    Args:
        text: Raw session text (user prompts, assistant responses)
        redact_patterns: Additional user-defined regex patterns

    Returns:
        (sanitized_text, was_redacted)
    """
    was_redacted = False

    # Built-in patterns (run first)
    builtin_patterns = [
        r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
        r'sk-ant-[a-zA-Z0-9\-]{95}',  # Anthropic API keys
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal access tokens
        r'Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*',  # Bearer tokens
        r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]+?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----',  # SSH keys
        r'(?:password|passwd|pwd)[\s]*[:=][\s]*[^\s]+',  # Password assignments
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',  # Email addresses (PII)
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN (US)
        r'\b\d{16}\b',  # Credit card numbers
    ]

    all_patterns = builtin_patterns + redact_patterns

    for pattern in all_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
            was_redacted = True

    return text, was_redacted
```

**Embedding Pipeline Integration:**

```python
# Before generating embeddings
sanitized_text, was_redacted = sanitize_session_text(
    session_text,
    config.redact_patterns
)

# Generate embeddings via TEI
embeddings = await tei_client.embed(sanitized_text)

# Store in Qdrant with metadata flag
await qdrant_client.upsert(
    collection_name=config.collection_name,
    points=[{
        "id": session_id,
        "vector": embeddings,
        "payload": {
            "text": sanitized_text,
            "redacted": was_redacted,  # Flag for audit trail
            "session_id": session_id,
            "created_at": timestamp,
        }
    }]
)
```

**Security Guarantees:**
- Sanitization runs **before** TEI embedding generation (sensitive data never leaves host)
- Sanitization runs **before** Qdrant storage (no plaintext secrets in vector DB)
- Redaction is logged via `redacted` flag for compliance auditing
- User-defined patterns extend built-in protections

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile-First Web App                         │
│                    (Next.js 15 PWA)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Chat UI   │  │  Settings   │  │  Heartbeat/Cron Dashboard│ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + REST
┌──────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Query API  │  │  Skill API  │  │  Cron API   │             │
│  │  (existing) │  │  (existing) │  │  (new)      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│  ┌──────▼────────────────▼────────────────▼──────┐             │
│  │           Agent Orchestration Service          │             │
│  │  • Memory injection (TEI + Qdrant)             │             │
│  │  • Heartbeat scheduler                         │             │
│  │  • Cron job executor                           │             │
│  │  • Gotify notifications                        │             │
│  └──────────────────────┬───────────────────────┘             │
│                         │                                       │
│  ┌──────────────────────▼───────────────────────┐             │
│  │            Claude Code SDK                    │             │
│  │  • Full tool access (bash, fs, git, etc.)     │             │
│  │  • MCP server integration (existing)          │             │
│  │  • Session management (existing)              │             │
│  └──────────────────────────────────────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │   Redis     │  │ TEI + Qdrant│             │
│  │ • Sessions  │  │ • Cache     │  │ (existing)  │             │
│  │ • Cron jobs │  │ • Pub/Sub   │  │ :52000/:53333│            │
│  │ • Heartbeat │  │ • Skills DB │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Memory Bank │  │  Homelab    │  │   Gotify    │             │
│  │ ~/memory/   │  │  Skills     │  │ (existing)  │             │
│  │ bank/       │  │  (existing) │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌───────────────────────────────────────────────┐             │
│  │              synapse-mcp                       │             │
│  │  • Flux: Docker/Compose (40 operations)       │             │
│  │  • Scout: SSH/Files/ZFS (16 operations)       │             │
│  │  • Multi-host with auto-discovery             │             │
│  │  • Connection pooling + caching               │             │
│  └───────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Resilience & Failure Modes

The assistant must gracefully degrade when dependencies fail. This section documents expected behavior and fallback strategies.

### Dependency Failure Scenarios

**TEI (Text Embeddings Inference - localhost:52000)**

**Failure modes:**
- Service not running
- Connection timeout (>5s)
- Out of memory errors
- Model loading failure

**Fallback behavior:**
- Memory search: Fall back to keyword-based search (PostgreSQL full-text search)
- QMD search: Return empty results with error message
- Session search: Disabled until TEI recovers
- Heartbeat: Continue without memory injection

**Detection:**
```python
try:
    embeddings = await tei_client.embed(text, timeout=5.0)
except (ConnectionError, TimeoutError, httpx.RequestError):
    logger.warning("TEI unavailable, falling back to keyword search")
    return keyword_search(text)
```

**Qdrant (Vector Database - localhost:53333)**

**Failure modes:**
- Service not running
- Collection not initialized
- Out of disk space
- Query timeout

**Fallback behavior:**
- Memory retrieval: Use PostgreSQL metadata only (no semantic ranking)
- QMD/Session search: Return error, suggest indexing when service recovers
- Write operations: Queue in Redis for retry (max 1000 items, 24h TTL)

**Retry semantics:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def qdrant_upsert(points: list[QdrantPoint]) -> None:
    await qdrant_client.upsert(collection_name="memories", points=points)
```

**Claude Code SDK**

**Failure modes:**
- Rate limits (Claude API or MAX tier)
- Network interruption
- Model overload (queue full)

**Fallback behavior:**
- Heartbeat: Skip turn, log failure, retry next interval
- Cron jobs: Mark as failed, retry based on job config (default: 3 retries, 5min backoff)
- Interactive queries: Return HTTP 503 with retry-after header

**Circuit breaker:**
```python
circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # Open after 5 consecutive failures
    recovery_timeout=60,  # Try again after 60s
    expected_exception=ClaudeAPIError
)

@circuit_breaker
async def execute_query(prompt: str) -> QueryResponse:
    return await sdk_client.query(prompt)
```

**Gotify (Push Notifications)**

**Failure modes:**
- Service unreachable
- Invalid token
- Message queue full

**Fallback behavior:**
- Queue messages in Redis (max 100/user, 7d TTL)
- Retry with exponential backoff (max 3 attempts)
- Log to PostgreSQL as notification history
- Do NOT block heartbeat/cron execution

**Queueing:**
```python
if not gotify_available:
    await redis.lpush(
        f"notification_queue:{user_id}",
        json.dumps({"message": msg, "priority": priority, "timestamp": now()})
    )
    await redis.expire(f"notification_queue:{user_id}", 604800)  # 7 days
```

**PostgreSQL (Primary Database)**

**Failure modes:**
- Connection pool exhausted
- Deadlock on concurrent writes
- Disk full

**Fallback behavior:**
- Read-only mode: Serve cached data from Redis
- Write operations: Return HTTP 503, client must retry
- Transactional rollback: All writes are atomic, no partial state

**Connection pooling:**
```python
# SQLAlchemy async engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1h
)
```

**Redis (Cache Layer)**

**Failure modes:**
- Cache miss (cold start)
- Eviction due to memory pressure
- Connection timeout

**Fallback behavior:**
- Rebuild from PostgreSQL (slower, but complete)
- Session cache: Create new ephemeral session
- Skill cache: Re-scan filesystem
- No queueing for cache failures (not critical path)

**Cache warming:**
```python
async def warm_cache_on_startup():
    """Warm critical caches after Redis restart."""
    await cache_skills()  # Scan ~/.claude/skills
    await cache_recent_sessions(limit=50)  # Last 50 sessions
    await cache_heartbeat_config()
```

### Timeout Settings

| Dependency | Connect Timeout | Request Timeout | Retry Count |
|------------|----------------|-----------------|-------------|
| TEI | 3s | 30s | 2 |
| Qdrant | 3s | 10s | 3 |
| Claude SDK | 5s | 120s (2min) | 1 |
| Gotify | 2s | 5s | 3 |
| PostgreSQL | 5s | 30s | 0 (fail fast) |
| Redis | 1s | 3s | 2 |

### Health Check Endpoints

**GET /api/v1/health**

Returns system health status:
```json
{
  "status": "healthy|degraded|unhealthy",
  "services": {
    "tei": {"status": "up|down", "latency_ms": 45},
    "qdrant": {"status": "up|down", "latency_ms": 12},
    "postgres": {"status": "up|down", "latency_ms": 8},
    "redis": {"status": "up|down", "latency_ms": 2},
    "gotify": {"status": "up|down", "latency_ms": 150}
  },
  "degraded_features": ["semantic_search", "notifications"]
}
```

**Health states:**
- `healthy`: All services operational
- `degraded`: Core functionality available, some features disabled
- `unhealthy`: Critical services down (PostgreSQL, Redis)

## Authentication & Authorization

All API endpoints require authentication via API key. This section documents auth requirements, scoping rules, and elevated permissions.

### API Key Authentication

**Required for all endpoints:**
```http
X-API-Key: <api_key>
```

**OR (OpenAI compatibility):**
```http
Authorization: Bearer <api_key>
```

**Middleware priority:**
1. `ApiKeyAuthMiddleware` (extracts `X-API-Key` header)
2. `BearerAuthMiddleware` (extracts `Authorization: Bearer`, only for `/v1/*` routes)

**Error responses:**
- `401 Unauthorized`: Missing or invalid API key
- `403 Forbidden`: Valid API key, but insufficient permissions

### API Key Storage

**Database schema (PostgreSQL):**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash
    owner_api_key VARCHAR(255) NOT NULL,   -- Plaintext, used for scoping
    owner_api_key_hash VARCHAR(64) NOT NULL,  -- SHA-256 hash for lookups
    name VARCHAR(255),
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_api_keys_owner_hash ON api_keys(owner_api_key_hash);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

**Usage patterns:**
- **Incoming request**: Hash provided API key → lookup via `key_hash` → retrieve `owner_api_key`
- **Scoping queries**: Use `owner_api_key` (plaintext) to filter user data
- **Cache key**: `session:{owner_api_key}:{session_id}` (Redis uses plaintext for scoping)

**Security note:** `owner_api_key` is stored in plaintext to enable scoping. `key_hash` protects the actual authentication credential.

### Scoping Rules

All user data is scoped to `owner_api_key`:

| Resource | Scope |
|----------|-------|
| Sessions | `owner_api_key` |
| Skills (database) | `owner_api_key` |
| Memories | `owner_api_key` |
| Cron jobs | `owner_api_key` |
| Heartbeat config | `owner_api_key` |
| MCP servers (API-key tier) | `owner_api_key` |
| Notification queue | `owner_api_key` |

**Example query:**
```python
async def get_user_sessions(owner_api_key: str) -> list[Session]:
    """Retrieve sessions scoped to owner_api_key."""
    result = await db.execute(
        select(Session).where(Session.owner_api_key == owner_api_key)
    )
    return result.scalars().all()
```

**Cross-tenant isolation:**
- API keys CANNOT access data from other `owner_api_key` values
- Redis keys MUST include `owner_api_key` prefix
- Qdrant filters MUST include `owner_api_key` in payload

### Elevated Permissions

Some endpoints require explicit permissions beyond basic authentication:

**Elevated endpoints:**

| Endpoint | Permission | Reason |
|----------|------------|--------|
| `POST /api/v1/devices/{name}/exec` | `device:execute` | Arbitrary command execution on SSH hosts |
| `GET /api/v1/infrastructure/hosts/{host}/logs/journal` | `logs:read` | Sensitive system logs (auth, sudo) |
| `POST /api/v1/cron` | `cron:manage` | Scheduled autonomous actions |
| `POST /api/v1/heartbeat/trigger` | `heartbeat:trigger` | Manual proactive checks |

**Permissions schema (JSONB):**
```json
{
  "device:execute": true,
  "logs:read": true,
  "cron:manage": true,
  "heartbeat:trigger": false
}
```

**Default permissions (new API keys):**
- All read operations: `true`
- Write operations: `true` (scoped to owner)
- Elevated operations: `false` (must be explicitly granted)

**Permission check:**
```python
def require_permission(permission: str):
    """Decorator to enforce permission check."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            api_key = request.state.api_key
            if not api_key.permissions.get(permission, False):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

@router.post("/devices/{name}/exec")
@require_permission("device:execute")
async def execute_device_command(...):
    ...
```

### Token Rotation

**Manual rotation:**
```http
POST /api/v1/api-keys/{id}/rotate
X-API-Key: <current_key>

Response:
{
  "new_key": "ak_...",
  "expires_at": "2026-03-01T00:00:00Z"
}
```

**Automatic expiration:**
- Optional `expires_at` timestamp per key
- Background job checks expiration daily
- Expired keys return `401 Unauthorized`

**Best practices:**
- Rotate keys every 90 days for production use
- Use short-lived keys (7-30 days) for CI/CD
- Revoke immediately on suspected compromise

### Rate Limiting

**Per API key limits:**
- Interactive queries: 60 requests/minute
- Heartbeat triggers: 10 requests/hour
- Session creation: 20 requests/minute

**Rate limit headers:**
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1643673600
```

**429 Too Many Requests response:**
```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Rate limit exceeded for API key",
    "retry_after": 42
  }
}
```

**Exempt endpoints (no rate limit):**
- `GET /api/v1/health`
- `GET /api/v1/docs` (OpenAPI spec)

## OpenClaw Feature Parity

We've achieved near-complete OpenClaw feature coverage through skills and configuration:

| OpenClaw Feature | Our Solution | Status |
|------------------|--------------|--------|
| WhatsApp, Telegram, Discord, Slack, iMessage | **claw-me-maybe** (Beeper unified messaging) | ✅ |
| Multi-model support (GPT, Gemini, Ollama) | **LLM Gateway** env vars + **gemini** skill | ✅ |
| Gateway/Control UI/Daemon architecture | Single FastAPI + Next.js (simpler) | ✅ |
| Multi-node remote execution | **synapse-mcp** (56 ops) + SSH skills | ✅ |
| Docker management | **synapse-mcp** Flux tool (40 ops) | ✅ |
| Skills/Plugin system | AgentSkills spec + **clawdhub** + **skillbox** | ✅ |
| Vector embeddings | TEI + Qdrant (already running) | ✅ |
| Push notifications | Gotify (existing homelab) | ✅ |
| Browser automation | Chrome + **agent-browser** + **browsh** | ✅ |
| Desktop control | **windows-control** + **computer-use** | ✅ |
| Smart home | **google-home-control** + homeassistant | ✅ |
| Social media | **twitter** + **reddit-scraper** | ✅ |
| Password management | **bitwarden** | ✅ |
| Automation orchestration | **clawflows** (109+ automations) | ✅ |

**What we're choosing NOT to build** (simplicity over complexity):
- Kubernetes/Swarm orchestration → Docker Compose is sufficient
- Multi-daemon architecture → Only needed for HA; personal assistant restarts fine

Everything else OpenClaw does? We can do it too.

## Ecosystem Compatibility

Because we follow the AgentSkills spec, we can use:
- Any skill from clawhub.com
- Claude Code's built-in skills
- OpenClaw community skills
- Custom skills following the spec
- **Existing homelab skills** (tailscale, unifi, unraid, media stack, etc.)

### Skillbox - Skill Management Layer

**[skillbox](https://github.com/christiananagnostou/skillbox/)** is a local-first, agent-agnostic skills manager.

**What it provides:**
- Central skill repository at `~/.config/skillbox/skills/`
- Install skills from GitHub/ClawHub: `skillbox add owner/repo`
- Auto-sync to multiple agents (Claude Code, Cursor, our API)
- Version management and updates: `skillbox status`, `skillbox update`

**Why we use it:**
- No need to build our own skill installer
- Handles multi-agent sync automatically
- Community-maintained, agent-agnostic
- JSON output for automation

**Integration with our API:**
```python
# Read skills from skillbox's canonical location
SKILLBOX_PATH = Path.home() / ".config" / "skillbox" / "skills"

# Existing QueryEnrichmentService already handles injection
# Just need to add skillbox path to skill discovery
```

### Planned Community Skills (from ClawHub)

| Skill | Downloads | Purpose |
|-------|-----------|---------|
| **gog** | - | Google Workspace (Gmail, Calendar, Drive, Contacts, Sheets, Docs) |
| **caldav** | - | CalDAV calendars (iCloud, Fastmail, Nextcloud) via vdirsyncer + khal |
| **weather** | 4,186 | Weather + forecasts (no API key required) - heartbeat awareness |
| **hackernews** | 18 | Browse/search Hacker News, job postings, tech news awareness |
| **morning-email-rollup** | 609 | Daily email + calendar digest pattern for heartbeat |
| **daily-recap** | 269 | Weather-aware daily summaries, cron-driven |
| **adhd-assistant** | 63 | Task breakdown, prioritization, time management |
| **zero-trust** | 12 | Security-first behavioral guidelines for cautious agent operation |
| **windows-control** | - | Full Windows desktop control (mouse, keyboard, screenshots, interact with any Windows app) |
| **computer-use** | - | Headless Linux desktop control via Xvfb+XFCE (17 actions, VNC remote viewing) |
| **clawflows** | - | Multi-skill automation orchestration (109+ automations, skill-agnostic) |
| **yt-video-downloader** | - | Download YouTube videos/playlists, extract audio, multiple formats/qualities |
| **clawdhub** | - | ClawdHub CLI (steipete) - search, install, update, publish skills |
| **twitter** | - | Twitter/X - post tweets, read timeline, manage followers, engagement metrics |
| **browsh** | - | Text-based browser using headless Firefox - web browsing in terminal/headless environments |
| **bitwarden** | - | Bitwarden/Vaultwarden password management via rbw CLI |
| **agent-browser** | - | Rust headless browser automation CLI (navigate, click, type, snapshot) for AI agents |
| **adguard** | - | AdGuard Home DNS filtering - manage blocklists/allowlists, stats, toggle protection |
| **reddit-scraper** | - | Read/search Reddit posts via old.reddit.com scraping (read-only research) |
| **youtube-transcript** | - | Fetch/summarize YouTube video transcripts (bypasses cloud IP blocks) |
| **skill-creator** | - | Guide for creating new skills - templates, best practices, tool integrations |
| **mcporter** | - | MCP server management (steipete) - list, configure, auth, call HTTP/stdio servers |
| **gemini** | - | Gemini CLI (steipete) - one-shot Q&A, summaries, text generation |
| **notebooklm-cli** | - | Google NotebookLM CLI - manage notebooks, sources, audio overviews |
| **tldr** | - | Simplified man pages from tldr-pages - quick CLI tool reference |
| **create-cli** | - | CLI design guide (steipete) - args, flags, subcommands, help, error handling |
| **openai-docs** | - | Query OpenAI developer docs via MCP - APIs, SDKs, Codex, rate limits |
| **codexmonitor** | - | Monitor/inspect local OpenAI Codex sessions (CLI + VS Code) |
| **google-home-control** | - | Smart home control via Google Assistant SDK (lights, TV, etc.) |
| **local-places** | - | Google Places search (steipete) - restaurants, cafes, nearby venues |
| **claw-me-maybe** | - | Beeper multi-platform messaging (WhatsApp, Telegram, Signal, Discord, Slack, iMessage, LinkedIn, FB, etc.) |

### ClawFlows - Automation Orchestration Layer

**[ClawFlows](https://clawflows.com)** is a registry of 109+ capability-based automations for AI agents.

**Core Philosophy**: Skill-agnostic automations using abstract interfaces (capabilities) that map to concrete skill implementations. "Write once, run anywhere" - automations don't break when you switch underlying skills.

**Capability → Skill Mapping:**

```text
Capability (abstract)       →    Skill (concrete implementation)
───────────────────────────────────────────────────────────────
calendar.list_events        →    gog, caldav, google-calendar
email.send                  →    gog, email, gmail, agentmail
database.query              →    sqlite, postgres, supabase
social.search               →    twitter, x-search
```

**Standard Capabilities (Building Blocks):**
- Prediction markets (Polymarket, Kalshi)
- Database operations (SQLite, storage)
- Chart generation
- Social media search (X/Twitter)
- Calendar/scheduling
- Text-to-speech

**Integration with our system:**
- Pre-built automations for heartbeat/cron patterns (morning briefings, daily recaps)
- Abstracts away which email/calendar skill is installed
- Community-maintained automation library (109+ and growing)
- Agent-driven automation creation (AI writes YAML, docs, opens PR)

**Control Surface:**

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Control Surface                                   │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│ Chrome          │ windows-control │ computer-use    │ synapse-mcp           │
│ (Web/Browser)   │ (Windows Apps)  │ (Linux Desktop) │ (Infrastructure)      │
│ • Navigate      │ • Mouse control │ • Xvfb virtual  │ • Docker/Compose      │
│ • Click/fill    │ • Keyboard      │   display       │ • SSH/Files/ZFS       │
│ • Extract data  │ • Screenshots   │ • Mouse/keyboard│ • Multi-host          │
│ • Auth'd apps   │ • Any Windows   │ • Screenshots   │ • 56 operations       │
│                 │   application   │ • VNC remote    │                       │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

Full desktop automation across all platforms: Chrome (web), windows-control (Windows), computer-use (Linux headless), synapse-mcp (infrastructure).

**Top ClawHub Skills by Downloads (reference):**

| Skill | Downloads | Description |
|-------|-----------|-------------|
| github | 4,500 | `gh` CLI for issues, PRs, CI runs |
| weather | 4,186 | Weather + forecasts (no API key) |
| homeassistant | 3,608 | Smart home control |
| slack | 1,897 | Slack messaging |
| email | 1,615 | Multi-provider email management |
| trello | 1,517 | Board/card management |
| agentmail | 907 | API-first email for AI agents |
| github-pr | 616 | Test PRs locally before merge |
| docker-essentials | 565 | Container management |
| deepwiki | 443 | GitHub repo documentation |

**Note:** Many ClawHub skills duplicate functionality we already have:
- `synapse-mcp` provides Docker/SSH operations (skip docker-essentials, portainer)
- `gog` provides Gmail/Calendar (skip email, gmail skills)
- Existing homelab skills cover infrastructure monitoring

Skills/MCP servers are plug-and-play across:
- Our personal assistant
- Claude Code
- OpenClaw
- Any AgentSkills-compatible agent

## API Surface

### Agent Endpoints (Existing)

```http
POST   /api/v1/query                     # Single query
POST   /api/v1/stream                    # SSE streaming
GET    /api/v1/sessions                  # List sessions
POST   /api/v1/sessions                  # Create session
GET    /api/v1/sessions/{id}             # Get session
DELETE /api/v1/sessions/{id}             # Delete session
```

### Skills Endpoints (Existing)

```http
GET    /api/v1/skills                    # List available skills
POST   /api/v1/skills                    # Create skill (database)
GET    /api/v1/skills/{id}               # Get skill details
PUT    /api/v1/skills/{id}               # Update skill (database)
DELETE /api/v1/skills/{id}               # Delete skill (database)
```

### Memory Endpoints (New)

```http
GET    /api/v1/memories                      # List all memories for user
POST   /api/v1/memories                      # Add memory (from conversation)
POST   /api/v1/memories/search               # Search memories (semantic)
DELETE /api/v1/memories/{memory_id}          # Delete single memory
DELETE /api/v1/memories                      # Delete ALL memories for user
```

#### POST /api/v1/memories

Add a new memory by extracting from conversation text.

**Request:**
```json
{
  "messages": "User prefers technical explanations with code examples",
  "metadata": {
    "category": "preferences",
    "source": "conversation"
  },
  "enable_graph": true
}
```

**Response:** `201 Created`
```json
{
  "memories": [
    {
      "id": "mem_abc123",
      "memory": "User prefers technical explanations with code examples",
      "hash": "sha256_hash",
      "created_at": "2026-02-06T22:30:00Z",
      "updated_at": "2026-02-06T22:30:00Z",
      "user_id": "hashed_api_key",
      "agent_id": "main",
      "metadata": {
        "category": "preferences",
        "source": "conversation"
      }
    }
  ],
  "count": 1
}
```

#### POST /api/v1/memories/search

Search memories using semantic similarity with optional graph context.

**Request:**
```json
{
  "query": "What are the user's coding preferences?",
  "limit": 5,
  "enable_graph": true
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "mem_abc123",
      "memory": "User prefers technical explanations with code examples",
      "score": 0.92,
      "metadata": {
        "category": "preferences",
        "source": "conversation"
      }
    },
    {
      "id": "mem_def456",
      "memory": "User works primarily with Python and TypeScript",
      "score": 0.87,
      "metadata": {
        "category": "tech_stack"
      }
    }
  ],
  "count": 2
}
```

#### GET /api/v1/memories

List all memories for the authenticated user.

**Response:** `200 OK`
```json
{
  "memories": [
    {
      "id": "mem_abc123",
      "memory": "User prefers technical explanations with code examples",
      "hash": "sha256_hash",
      "created_at": "2026-02-06T22:30:00Z",
      "updated_at": "2026-02-06T22:30:00Z",
      "user_id": "hashed_api_key",
      "agent_id": "main",
      "metadata": {
        "category": "preferences"
      }
    }
  ],
  "count": 1
}
```

#### DELETE /api/v1/memories/{memory_id}

Delete a specific memory by ID.

**Response:** `200 OK`
```json
{
  "deleted": true,
  "message": "Memory mem_abc123 deleted"
}
```

#### DELETE /api/v1/memories

Delete all memories for the authenticated user.

**Response:** `200 OK`
```json
{
  "deleted": true,
  "message": "All memories deleted"
}
```

### Heartbeat Endpoints (New)

```http
GET    /api/v1/heartbeat/config          # Get heartbeat config
PUT    /api/v1/heartbeat/config          # Update heartbeat config
POST   /api/v1/heartbeat/trigger         # Trigger immediate heartbeat
GET    /api/v1/heartbeat/history         # Get heartbeat history
```

### Cron Endpoints (New)

```http
GET    /api/v1/cron                      # List cron jobs
POST   /api/v1/cron                      # Create cron job
GET    /api/v1/cron/{id}                 # Get cron job
PUT    /api/v1/cron/{id}                 # Update cron job
DELETE /api/v1/cron/{id}                 # Delete cron job
POST   /api/v1/cron/{id}/run             # Trigger immediate run
GET    /api/v1/cron/{id}/history         # Get run history
```

### QMD Endpoints (New)

```http
POST   /api/v1/qmd/index                 # Index markdown directory
GET    /api/v1/qmd/search                # Semantic search markdown files
GET    /api/v1/qmd/status                # Indexing status
```

### Session Search Endpoints (New)

```http
POST   /api/v1/session-search/index      # Index Claude sessions
GET    /api/v1/session-search/search     # Search past sessions
GET    /api/v1/session-search/status     # Indexing status
```

### Device Endpoints (New)

```http
GET    /api/v1/devices                   # List devices (from memory bank)
GET    /api/v1/devices/{name}            # Get device details
POST   /api/v1/devices/{name}/exec       # Execute command on device
GET    /api/v1/devices/inventory/refresh # Refresh SSH inventory
```

### Infrastructure Endpoints (New - via synapse-mcp)

```http
GET    /api/v1/infrastructure/containers                  # List containers (all hosts)
GET    /api/v1/infrastructure/containers/{name}/logs      # Container logs with grep
GET    /api/v1/infrastructure/compose                     # List Compose projects
GET    /api/v1/infrastructure/compose/{project}/status    # Compose project status
GET    /api/v1/infrastructure/hosts/{host}/resources      # CPU/memory/disk usage
GET    /api/v1/infrastructure/hosts/{host}/zfs/pools      # ZFS pool health
GET    /api/v1/infrastructure/hosts/{host}/logs/journal   # systemd journal logs
```

### Persona Endpoints (New)

```http
GET    /api/v1/persona                   # Get persona config
PUT    /api/v1/persona                   # Update persona config
```

**Storage Strategy:**

Persona configuration uses **PostgreSQL as primary storage** with JSON file fallback for single-user deployments:

- **Multi-User (Default)**: PostgreSQL database with API key scoping
- **Single-User (Fallback)**: `~/.config/assistant/persona.json` when `DATABASE_URL` not set

**Database Schema:**

```sql
-- Migration: xxx_add_persona_config.py
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

-- Index for API key lookups
CREATE INDEX idx_persona_config_api_key ON persona_config(owner_api_key_hash);

-- Trigger for updated_at
CREATE TRIGGER update_persona_config_updated_at
    BEFORE UPDATE ON persona_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Configuration Structure:**

```json
{
  "name": "Jarvis",
  "personality": "helpful, concise, proactive",
  "communication_style": "professional but warm",
  "expertise_areas": ["homelab", "automation", "development"],
  "proactivity": "medium",
  "verbosity": "balanced",
  "formality": "balanced",
  "use_emoji": false,
  "custom_instructions": "Always prioritize security and modularity"
}
```

**File-Based Mode (Single-User Deployments):**

When `DATABASE_URL` is not configured, the service reads/writes to `~/.config/assistant/persona.json`. This mode is intended for personal/development use where multi-tenant isolation is not required.

**Decision Logic:**

```python
# apps/api/services/persona_service.py
from pathlib import Path
import json

class PersonaService:
    """Persona configuration management with dual storage."""

    def __init__(self, db_session: AsyncSession | None, config: Settings):
        self.db = db_session
        self.config = config
        self.file_path = Path.home() / ".config" / "assistant" / "persona.json"

    async def get_persona(self, api_key_hash: str) -> PersonaConfig:
        """Get persona config from database or file."""
        if self.db is not None:
            # PostgreSQL mode (multi-user)
            result = await self.db.execute(
                select(PersonaConfigModel).where(
                    PersonaConfigModel.owner_api_key_hash == api_key_hash
                )
            )
            model = result.scalar_one_or_none()
            if model:
                return PersonaConfig.from_orm(model)
            # Return defaults if not found
            return PersonaConfig()
        else:
            # File mode (single-user)
            if self.file_path.exists():
                data = json.loads(self.file_path.read_text())
                return PersonaConfig(**data)
            return PersonaConfig()

    async def update_persona(
        self,
        api_key_hash: str,
        updates: PersonaUpdate,
    ) -> PersonaConfig:
        """Update persona config in database or file."""
        if self.db is not None:
            # PostgreSQL mode
            result = await self.db.execute(
                select(PersonaConfigModel).where(
                    PersonaConfigModel.owner_api_key_hash == api_key_hash
                )
            )
            model = result.scalar_one_or_none()
            if not model:
                # Create new record
                model = PersonaConfigModel(owner_api_key_hash=api_key_hash)
                self.db.add(model)

            # Apply updates
            for field, value in updates.dict(exclude_unset=True).items():
                setattr(model, field, value)

            await self.db.commit()
            await self.db.refresh(model)
            return PersonaConfig.from_orm(model)
        else:
            # File mode
            current = await self.get_persona(api_key_hash)
            updated = current.copy(update=updates.dict(exclude_unset=True))

            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(updated.json(indent=2))
            return updated
```

## Implementation Phases

### Phase 1: Memory System Integration

- Integrate Mem0 OSS library with multi-store configuration
- Configure LLM (Gemini 3 Flash Preview) for entity extraction
- Configure embedder (Qwen/Qwen3-Embedding-0.6B via TEI at 100.74.16.82:52000)
- Configure vector store (Qdrant at localhost:53333)
- Configure graph store (Neo4j at localhost:54687)
- Memory service wrapper for mem0.Memory API (add, search, get_all, update, delete)
- Memory injection into prompts (search → inject → add flow)
- Memory CRUD API endpoints with multi-tenant isolation (user_id scoping)
- Graph memory toggle (enable_graph parameter)

### Phase 2: Heartbeat System

- Background scheduler (APScheduler)
- HEARTBEAT.md loading and parsing
- Active hours support
- **Gotify integration** (use existing homelab skill)
- Heartbeat history logging

### Phase 3: Cron Jobs
- Cron job storage (PostgreSQL)
- APScheduler with cron triggers
- Main vs isolated session modes
- Job CRUD API endpoints
- **Gotify notifications** for delivery

### Phase 4: QMD (Query Markup Documents)
- Skill for markdown semantic search
- Hook for auto-indexing new files
- Integration with existing Qdrant collection
- Search API endpoints

### Phase 5: Session Search
- JSONL session parser
- Incremental indexing
- Search API endpoints
- Context retrieval for queries

### Phase 6: Device Management API
- Read device inventory from `~/memory/bank/ssh/`
- API endpoints for device queries
- Command execution endpoint (with confirmation)
- Integration with homelab SSH execution

### Phase 7: Web App
- Next.js 15 PWA
- Mobile-first responsive design
- Chat interface with streaming
- Settings/config UI
- Heartbeat/cron dashboard

## Testing Requirements

### Coverage Targets

| Test Type | Target | Purpose |
|-----------|--------|---------|
| **Unit Tests** | ≥90% | Individual functions/classes in isolation |
| **Integration Tests** | ≥80% | Multi-component interactions with real services |
| **Contract Tests** | 100% | API endpoint compliance with OpenAPI spec |
| **E2E Tests** | Critical paths only | User-facing workflows in staging environment |

**Overall target**: ≥85% combined coverage across all test types.

### Testing Pyramid

```text
           ┌─────────┐
          ╱   E2E    ╲    ~5% (Critical user flows)
         ╱ (Slow)     ╲
        ┌─────────────┐
       ╱ Integration   ╲  ~25% (Service boundaries)
      ╱  (Medium)       ╲
     ┌───────────────────┐
    ╱      Unit Tests     ╲ ~70% (Business logic)
   ╱      (Fast)           ╱
  └─────────────────────┘
```

**Distribution rationale:**

- **Unit tests (70%)**: Fast execution, comprehensive business logic coverage, isolated dependencies
- **Integration tests (25%)**: Service boundaries, database operations, external APIs
- **E2E tests (5%)**: Critical user workflows (heartbeat, cron execution, chat streaming)

**Speed targets:**

- Unit tests: <10s total execution
- Integration tests: <60s total execution
- E2E tests: <5min total execution

### Test Isolation

#### Unit Tests

**Requirements:**
- Mock ALL external dependencies (database, Redis, Claude SDK, TEI, Qdrant, Gotify)
- No network calls (use mocked responses)
- No file system I/O (use in-memory fixtures)
- Fast execution (<100ms per test)
- Independent of execution order

**Example (mocking dependencies):**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from apps.api.services.memory.service import MemoryService

@pytest.fixture
def mock_mem0():
    """Mock Mem0 Memory client."""
    mock = MagicMock()
    mock.add = AsyncMock(return_value=[{
        "id": "mem_123",
        "memory": "User prefers Python",
        "hash": "abc123"
    }])
    mock.search = AsyncMock(return_value=[{
        "id": "mem_123",
        "memory": "User prefers Python",
        "score": 0.95
    }])
    return mock

@pytest.fixture
def memory_service(mock_mem0):
    """MemoryService with mocked dependencies."""
    return MemoryService(memory_client=mock_mem0)

async def test_add_memory(memory_service, mock_mem0):
    """Test adding a new memory."""
    # Arrange
    api_key = "test-key"
    messages = "User prefers Python for backend development"

    # Act
    result = await memory_service.add_memory(
        api_key=api_key,
        messages=messages,
        metadata={"category": "preferences"}
    )

    # Assert
    assert result["count"] == 1
    assert result["memories"][0]["memory"] == "User prefers Python"
    mock_mem0.add.assert_called_once_with(
        messages=messages,
        user_id=api_key,
        agent_id="main",
        metadata={"category": "preferences"}
    )
```

#### Integration Tests

**Requirements:**
- Use test database (PostgreSQL with schema migrations applied)
- Use test Redis instance (separate from production)
- Clean state before each test (transactions with rollback)
- Use real service implementations where possible
- FileLock for coordinating test database access across pytest-xdist workers

**Example (test database with cleanup):**

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from apps.api.models import Base
from apps.api.config import Settings

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:54432/test_db"
    )
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def db_session(test_db_engine):
    """Provide clean database session per test."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            # Rollback after test (clean state)
            await session.rollback()

async def test_create_cron_job(db_session):
    """Test cron job creation with real database."""
    from apps.api.models import CronJob
    from datetime import datetime

    # Arrange
    job = CronJob(
        id="job_123",
        name="Daily backup",
        schedule={"type": "cron", "expression": "0 2 * * *"},
        session_mode="isolated",
        message="Run backup script",
        enabled=True
    )

    # Act
    db_session.add(job)
    await db_session.commit()

    # Assert (query from database)
    result = await db_session.execute(
        select(CronJob).where(CronJob.id == "job_123")
    )
    saved_job = result.scalar_one()
    assert saved_job.name == "Daily backup"
    assert saved_job.enabled is True
```

**FileLock coordination (pytest-xdist):**

```python
# tests/conftest.py
import pytest
from filelock import FileLock

@pytest.fixture(scope="session")
def test_db_lock(tmp_path_factory):
    """File lock for coordinating test database migrations."""
    lock_file = tmp_path_factory.getbasetemp().parent / "test_db.lock"
    return FileLock(str(lock_file))

@pytest.fixture(scope="session")
async def test_db_engine(test_db_lock):
    """Create test database with migration coordination."""
    # Acquire lock before migrations
    with test_db_lock:
        # Only one worker runs migrations
        engine = create_async_engine(DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()
```

#### E2E Tests

**Requirements:**
- Run against staging environment (not production)
- Use real database and services (no mocks)
- Playwright for browser automation
- Mark with `@pytest.mark.e2e` (excluded from default runs)
- Slow execution acceptable (user-facing workflows)

**Example (heartbeat execution E2E):**

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
async def test_heartbeat_execution_flow():
    """E2E test: Heartbeat triggers and sends Gotify notification."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Step 1: Login to web app
        await page.goto("http://localhost:53000/login")
        await page.fill("input[name=api_key]", "test-api-key")
        await page.click("button[type=submit]")

        # Step 2: Navigate to heartbeat config
        await page.goto("http://localhost:53000/heartbeat")
        await page.wait_for_selector("h1:has-text('Heartbeat')")

        # Step 3: Trigger manual heartbeat
        await page.click("button:has-text('Trigger Now')")

        # Step 4: Wait for execution to complete
        await page.wait_for_selector(
            ".heartbeat-status:has-text('Completed')",
            timeout=30000  # 30s timeout
        )

        # Step 5: Verify notification sent (check history)
        await page.goto("http://localhost:53000/heartbeat/history")
        latest_run = await page.query_selector(".run-item:first-child")
        assert latest_run is not None

        status = await latest_run.query_selector(".status")
        assert await status.inner_text() == "Completed"

        await browser.close()
```

### TDD Workflow

All new features and bug fixes MUST follow Test-Driven Development:

**Process:**

1. **RED**: Write a failing test that describes the desired behavior
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code quality while keeping tests green

**Example (adding memory search limit parameter):**

```python
# Step 1: RED - Write failing test
async def test_memory_search_with_limit(memory_service):
    """Memory search should respect limit parameter."""
    # Arrange
    api_key = "test-key"
    # Assume 10 memories exist
    for i in range(10):
        await memory_service.add_memory(
            api_key=api_key,
            messages=f"Memory {i}"
        )

    # Act
    results = await memory_service.search_memories(
        api_key=api_key,
        query="Memory",
        limit=3  # Request only 3 results
    )

    # Assert
    assert len(results) == 3  # FAILS - limit not implemented yet

# Step 2: GREEN - Make test pass
class MemoryService:
    async def search_memories(
        self,
        api_key: str,
        query: str,
        limit: int = 10,  # Add limit parameter with default
    ) -> list[dict]:
        """Search memories with limit."""
        results = await self.memory_client.search(
            query=query,
            user_id=api_key,
            limit=limit  # Pass limit to mem0
        )
        return results  # Test now passes

# Step 3: REFACTOR - Improve implementation
class MemoryService:
    async def search_memories(
        self,
        api_key: str,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search memories using semantic similarity.

        Args:
            api_key: User API key for scoping
            query: Search query text
            limit: Maximum results to return (default: 10, max: 100)

        Returns:
            List of memory dictionaries with scores

        Raises:
            ValueError: If limit exceeds maximum
        """
        if limit > 100:
            raise ValueError("Limit cannot exceed 100")

        results = await self.memory_client.search(
            query=query,
            user_id=api_key,
            limit=limit
        )
        return results
```

### Test Naming Convention

**Pattern**: `test_<component>_<scenario>_<expected_outcome>`

**Good examples:**

```python
# Unit tests
test_memory_service_add_creates_embedding()
test_heartbeat_scheduler_skips_outside_active_hours()
test_cron_job_executor_retries_on_failure()
test_session_sanitizer_redacts_api_keys()

# Integration tests
test_query_endpoint_injects_memories_from_qdrant()
test_heartbeat_sends_gotify_notification()
test_cron_job_creates_isolated_session()

# E2E tests
test_user_chat_with_streaming_response()
test_heartbeat_execution_triggers_from_dashboard()
```

**Bad examples:**

```python
# Too vague
test_memory()
test_heartbeat()

# Not descriptive
test_service_1()
test_edge_case()

# Missing context
test_search()
test_failure()
```

### Mock Strategy

**What to mock (in unit tests):**

- External HTTP APIs (Claude SDK, TEI, Qdrant, Gotify)
- Database sessions (use mocked AsyncSession)
- File system operations (use in-memory buffers)
- Time-dependent logic (freeze time with `freezegun`)
- Random data generation (seed random for determinism)

**What NOT to mock:**

- Business logic functions (test the real implementation)
- Pure functions with no side effects
- In-memory data structures (lists, dicts, sets)
- Pydantic models and schemas

**Example (pytest fixture-based mocking):**

```python
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from freezegun import freeze_time

@pytest.fixture
def mock_claude_sdk():
    """Mock Claude SDK client."""
    with patch("apps.api.services.agent.service.ClaudeSDKClient") as mock:
        instance = mock.return_value
        instance.query = AsyncMock(return_value={
            "content": "Response text",
            "input_tokens": 100,
            "output_tokens": 50
        })
        yield instance

@pytest.fixture
def mock_gotify_client():
    """Mock Gotify notification client."""
    with patch("apps.api.services.notifications.GotifyClient") as mock:
        instance = mock.return_value
        instance.send = AsyncMock(return_value={"id": 123, "priority": 5})
        yield instance

@freeze_time("2026-02-06 14:30:00")
async def test_heartbeat_within_active_hours(mock_claude_sdk, mock_gotify_client):
    """Heartbeat executes during active hours."""
    from apps.api.services.heartbeat import HeartbeatService

    # Arrange
    config = HeartbeatConfig(
        enabled=True,
        active_hours=("08:00", "22:00"),  # 14:30 is within range
        interval_minutes=30
    )
    service = HeartbeatService(
        config=config,
        claude_client=mock_claude_sdk,
        gotify_client=mock_gotify_client
    )

    # Act
    result = await service.execute_heartbeat()

    # Assert
    assert result.status == "completed"
    mock_claude_sdk.query.assert_called_once()  # Heartbeat ran
```

### Continuous Integration

**Pre-commit Hooks (`.pre-commit-config.yaml`):**

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run unit tests
        entry: uv run pytest tests/unit -v
        language: system
        pass_filenames: false
        always_run: true

      - id: ruff-check
        name: Ruff linter
        entry: uv run ruff check .
        language: system
        types: [python]

      - id: ty-check
        name: Type checking
        entry: uv run ty check
        language: system
        types: [python]
```

**CI Pipeline (GitHub Actions example):**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run unit tests
        run: uv run pytest tests/unit -v --cov=apps/api --cov-report=xml

      - name: Run integration tests
        run: uv run pytest tests/integration -v

      - name: Check coverage threshold
        run: |
          uv run coverage report --fail-under=85

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

**Coverage enforcement:**

```toml
# pyproject.toml
[tool.coverage.run]
source = ["apps/api"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = false
```

### Test Data Management

**Fixtures for reusable test data:**

```python
# tests/conftest.py
import pytest
from datetime import datetime

@pytest.fixture
def sample_memory_data():
    """Sample memory data for tests."""
    return {
        "id": "mem_abc123",
        "memory": "User prefers Python for backend development",
        "hash": "sha256_hash_value",
        "created_at": datetime(2026, 2, 6, 14, 30),
        "updated_at": datetime(2026, 2, 6, 14, 30),
        "user_id": "hashed_api_key",
        "agent_id": "main",
        "metadata": {"category": "preferences"}
    }

@pytest.fixture
def sample_cron_job():
    """Sample cron job configuration."""
    return {
        "id": "job_daily_backup",
        "name": "Daily Backup",
        "schedule": {
            "type": "cron",
            "expression": "0 2 * * *"
        },
        "session_mode": "isolated",
        "message": "Run daily backup script",
        "enabled": True
    }

@pytest.fixture
def sample_heartbeat_config():
    """Sample heartbeat configuration."""
    return HeartbeatConfig(
        enabled=True,
        interval_minutes=30,
        active_hours=("08:00", "22:00"),
        timezone="America/New_York",
        checklist_path="~/.config/assistant/HEARTBEAT.md",
        notification_method="gotify"
    )
```

**Factory pattern for test objects:**

```python
# tests/factories.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class MemoryFactory:
    """Factory for creating test memory objects."""

    @staticmethod
    def create(
        memory_id: str = "mem_test",
        memory_text: str = "Test memory",
        user_id: str = "test-user",
        **kwargs: Any
    ) -> dict:
        """Create a memory dictionary with defaults."""
        return {
            "id": memory_id,
            "memory": memory_text,
            "hash": f"hash_{memory_id}",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "user_id": user_id,
            "agent_id": "main",
            "metadata": kwargs.get("metadata", {})
        }

    @staticmethod
    def create_batch(count: int, **kwargs: Any) -> list[dict]:
        """Create multiple memories with incremental IDs."""
        return [
            MemoryFactory.create(
                memory_id=f"mem_{i}",
                memory_text=f"Test memory {i}",
                **kwargs
            )
            for i in range(count)
        ]

# Usage in tests
def test_memory_search_pagination():
    """Test memory search with pagination."""
    # Create 20 test memories
    memories = MemoryFactory.create_batch(20, user_id="test-user")

    # Test first page
    page1 = memories[:10]
    assert len(page1) == 10

    # Test second page
    page2 = memories[10:]
    assert len(page2) == 10
```

### Performance Testing

**Load testing with Locust:**

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class APIUser(HttpUser):
    """Simulate API user load."""
    wait_time = between(1, 3)  # Wait 1-3s between requests

    def on_start(self):
        """Setup: Set API key header."""
        self.client.headers = {"X-API-Key": "test-key"}

    @task(3)  # Weight: 3x more common than other tasks
    def query_agent(self):
        """POST /api/v1/query endpoint."""
        self.client.post("/api/v1/query", json={
            "prompt": "What is the weather today?",
            "max_turns": 1
        })

    @task(1)
    def search_memories(self):
        """POST /api/v1/memories/search endpoint."""
        self.client.post("/api/v1/memories/search", json={
            "query": "user preferences",
            "limit": 5
        })

    @task(1)
    def list_sessions(self):
        """GET /api/v1/sessions endpoint."""
        self.client.get("/api/v1/sessions")

# Run: locust -f tests/performance/locustfile.py --host=http://localhost:54000
```

**Benchmark tests with pytest-benchmark:**

```python
import pytest

def test_memory_search_performance(benchmark, memory_service):
    """Benchmark memory search latency."""
    # Arrange
    api_key = "test-key"
    query = "user preferences"

    # Act & Assert
    result = benchmark(
        memory_service.search_memories,
        api_key=api_key,
        query=query,
        limit=10
    )

    # Verify performance target
    assert benchmark.stats.median < 0.2  # <200ms median latency
    assert len(result) <= 10
```

### Flaky Test Policy

**Zero tolerance for flaky tests.**

**Common causes:**

1. **Race conditions**: Use proper async/await, avoid `time.sleep()` in tests
2. **Non-deterministic data**: Seed random generators, freeze time with `freezegun`
3. **External service dependencies**: Mock all external APIs in unit tests
4. **Test interdependence**: Ensure tests clean up state, use transactions with rollback
5. **Timing assumptions**: Use `wait_for` patterns instead of fixed sleeps

**Example (fixing flaky test with wait_for):**

```python
# BAD: Flaky test with sleep
async def test_heartbeat_notification_flaky():
    """Flaky: Assumes 2s is enough for heartbeat execution."""
    service.trigger_heartbeat()
    await asyncio.sleep(2)  # Race condition!
    assert notification_sent is True  # May fail if heartbeat takes >2s

# GOOD: Reliable test with wait_for
async def test_heartbeat_notification_reliable():
    """Reliable: Wait for actual completion event."""
    event = asyncio.Event()

    async def wait_for_notification():
        while not notification_sent:
            await asyncio.sleep(0.1)  # Poll interval
        event.set()

    service.trigger_heartbeat()

    # Wait up to 10s for notification
    try:
        await asyncio.wait_for(event.wait(), timeout=10)
    except asyncio.TimeoutError:
        pytest.fail("Notification not sent within 10s")

    assert notification_sent is True  # Always reliable
```

**Detection and remediation:**

```bash
# Run tests 10 times to detect flakiness
for i in {1..10}; do
  uv run pytest tests/integration/test_heartbeat.py || echo "FAILED on run $i"
done

# If flaky, mark as such temporarily while fixing
@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_potentially_flaky():
    ...
```

**Policy**: Flaky tests MUST be fixed or removed within 48 hours of detection. Do not accumulate flaky tests in the codebase.

## Success Metrics

- **Simplicity**: Single `docker compose up` deployment
- **Compatibility**: 100% AgentSkills spec compliance
- **Performance**: Memory search < 200ms (via existing Qdrant)
- **Reliability**: 99.9% heartbeat execution success rate
- **Coverage**: 90% of OpenClaw use cases supported
- **Code Reuse**: Leverage 100% of existing cli-firecrawl and homelab infrastructure

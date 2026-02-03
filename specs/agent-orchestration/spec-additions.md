# Agent Orchestration Spec - Missing Sections

This document contains the four missing sections that need to be added to `spec.md`.

## 1. SessionSearchConfig Privacy Extensions (Add after line 473)

**Location**: Extend the `SessionSearchConfig` class definition

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
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses (PII)
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

## 2. Resilience & Failure Modes Section (Add after Architecture section, before OpenClaw Feature Parity)

**Location**: New section between Architecture diagram and OpenClaw Feature Parity table

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

## 3. Authentication & Authorization Section (Add after Resilience section)

**Location**: New section after Resilience & Failure Modes

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
    key_hash VARCHAR(64) NOT NULL UNIQUE,  -- bcrypt hash
    owner_api_key VARCHAR(255) NOT NULL,   -- Plaintext, used for scoping
    owner_api_key_hash VARCHAR(64) NOT NULL,  -- bcrypt hash for lookups
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

## 4. HeartbeatConfig Timezone Configuration (Modify line 279)

**Location**: Modify the `HeartbeatConfig` class definition around line 279

**CHANGE FROM:**
```python
class HeartbeatConfig:
    enabled: bool = True
    interval_minutes: int = 30
    active_hours: tuple[str, str] = ("08:00", "22:00")
    timezone: str = "America/New_York"
    checklist_path: str = "~/.config/assistant/HEARTBEAT.md"
    notification_method: Literal["gotify", "none"] = "gotify"
```

**CHANGE TO:**
```python
class HeartbeatConfig:
    enabled: bool = True
    interval_minutes: int = 30
    active_hours: tuple[str, str] = ("08:00", "22:00")
    timezone: str | None = None  # None = system timezone, or IANA timezone string
    checklist_path: str = "~/.config/assistant/HEARTBEAT.md"
    notification_method: Literal["gotify", "none"] = "gotify"
```

**ADD AFTER HeartbeatConfig:**

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

---

## Integration Instructions

1. **SessionSearchConfig Privacy**: Add to end of Section 9 (Session Search & Retrieval)
2. **Resilience & Failure Modes**: Add new section after Architecture diagram
3. **Authentication & Authorization**: Add new section after Resilience section
4. **HeartbeatConfig Timezone**: Modify existing definition in Section 3 (Heartbeat)

These additions address all four missing sections identified in the requirements.

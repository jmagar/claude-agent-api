# ADR-001: Distributed Session State Management

**Status:** Accepted
**Date:** 2026-01-09
**Deciders:** Engineering Team
**Context:** P0-1 (in-memory session state) and P0-2 (no PostgreSQL fallback)

## Context

The initial implementation stored active session state in-memory (`AgentService._active_sessions: dict[str, asyncio.Event]`) and session data only in Redis cache. This prevented:
- Horizontal scaling (sessions tied to single instance)
- Failover (server restart loses sessions)
- Data durability (Redis restart loses sessions)

## Decision

Migrate to **distributed session state** with:
1. Redis-backed active session tracking (replaces in-memory dict)
2. PostgreSQL as source of truth for session data
3. Redis as cache layer (cache-aside pattern)
4. Distributed locking for session operations
5. Redis pub/sub for interrupt signals (future enhancement)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ API Instance 1          API Instance 2              │
│ ┌─────────────┐        ┌─────────────┐            │
│ │AgentService │        │AgentService │            │
│ └──────┬──────┘        └──────┬──────┘            │
│        │                       │                   │
│        └───────────┬───────────┘                   │
│                    │                               │
│            ┌───────▼────────┐                      │
│            │ Redis (Shared) │                      │
│            │ - Active sessions (SET)               │
│            │ - Interrupt markers                   │
│            │ - Session cache                       │
│            └───────┬────────┘                      │
│                    │                               │
│            ┌───────▼────────┐                      │
│            │ PostgreSQL     │                      │
│            │ - sessions table (source of truth)   │
│            └────────────────┘                      │
└─────────────────────────────────────────────────────┘
```

## Implementation

### Active Session Tracking
- **Key:** `active_session:{session_id}`
- **Value:** `"true"` (existence = active)
- **TTL:** 7200 seconds (2 hours)
- **Operations:**
  - `_register_active_session()` - SET with TTL
  - `_is_session_active()` - EXISTS check
  - `_unregister_active_session()` - DEL

### Session Data Storage
- **Primary:** PostgreSQL `sessions` table
- **Cache:** Redis `session:{session_id}` keys
- **Pattern:** Cache-aside (read-through)
  1. Check cache first (fast path)
  2. On miss, query PostgreSQL
  3. Re-cache result (repopulate cache)

### Dual-Write on Create
1. Write to PostgreSQL first (durable)
2. Write to Redis cache second (fast)
3. If cache write fails, log warning but continue

### Interrupt Signaling
- **Key:** `interrupted:{session_id}`
- **Value:** `"true"`
- **TTL:** 300 seconds (5 minutes)
- **Future:** Redis pub/sub for real-time propagation

### Distributed Locking
- **Key:** `session_lock:{session_id}`
- **Value:** Unique lock owner ID (UUID)
- **TTL:** 5 seconds (operation timeout)
- **Purpose:** Prevent race conditions on concurrent updates

## Consequences

### Positive
- ✅ Horizontal scaling enabled (N instances)
- ✅ Failover support (sessions survive pod restarts)
- ✅ Data durability (PostgreSQL persistence)
- ✅ Graceful degradation (works without Redis)
- ✅ Performance optimized (Redis cache for hot path)

### Negative
- ⚠️ Increased complexity (dual-write, cache invalidation)
- ⚠️ Additional latency on cache miss (DB query)
- ⚠️ Requires Redis for optimal performance
- ⚠️ Lock contention possible under high load

### Mitigation
- Cache TTL tuned for session duration (2 hours)
- Lock timeout prevents deadlocks (5 seconds)
- Comprehensive logging for debugging
- Integration tests for multi-instance scenarios

### Cache Warming Strategy
After Redis restarts or cold starts, the cache will be empty. The system handles this gracefully:
- **Automatic Repopulation:** Cache-aside pattern automatically repopulates cache on first access
- **Expected Behavior:** Temporary increase in database queries until hot data is re-cached
- **Performance Impact:** First request to each session will be slower (database query)
- **Recovery Time:** Typically stabilizes within 5-10 minutes of normal traffic

**Optional Enhancement:** Implement proactive cache warming on startup:
1. Query most recently active sessions from PostgreSQL
2. Pre-populate Redis cache before accepting traffic
3. Reduces cold start impact on first requests
4. Add to deployment guide if cold start performance becomes critical

## Migration Path

1. Add Redis-backed session tracking (Task 1-2)
2. Implement PostgreSQL fallback (Task 3-4)
3. Add distributed locking (Task 6)
4. Update AgentService (Task 5)
5. Add integration tests (Task 8)
6. Deploy with Redis + PostgreSQL
7. Monitor cache hit rate and lock contention

## Monitoring

### Key Metrics

**Cache Performance:**
- `redis_session_hits` - Cache hit rate
- `redis_session_misses` - Cache miss rate
- `postgres_fallback_queries` - DB fallback frequency

**Distributed Operations:**
- `active_sessions_redis` - Active sessions in Redis
- `session_lock_acquisitions` - Lock acquisition rate
- `session_lock_timeouts` - Lock timeout frequency
- `interrupt_signals_sent` - Interrupt signal rate

**Performance:**
- `session_read_latency_ms` - Read operation latency
- `session_write_latency_ms` - Write operation latency
- `session_cache_repopulation_ms` - Cache miss recovery time

### Logging

All session operations include structured logging with:
- `session_id` - Session identifier
- `storage` - Storage backend (redis/postgres)
- `distributed` - Whether operation is distributed
- `operation` - Operation type (create/read/update/delete)

Example log output:
```json
{
  "timestamp": "2026-01-09T10:15:30Z",
  "level": "info",
  "message": "Session retrieved from database and re-cached",
  "session_id": "abc-123",
  "model": "sonnet",
  "storage": "postgres",
  "distributed": true
}
```

## References

- P0-1: In-Memory Session State Prevents Horizontal Scaling
- P0-2: Missing PostgreSQL Session Fallback
- Comprehensive Review Report (2026-01-09)

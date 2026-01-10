# ADR-001: Distributed Session State

## Context

The API needs to support concurrent sessions across multiple instances while
remaining resilient to cache outages. We need fast reads for active sessions
and durable storage for auditing and recovery.

## Decision

Use PostgreSQL as the source of truth for session data and Redis as a cache
layer for fast reads and distributed coordination. The service uses a
cache-aside pattern and rehydrates Redis entries on cache misses.

## Consequences

- Redis provides low-latency reads and distributed locking for session updates.
- PostgreSQL guarantees durability and enables recovery after Redis restarts.
- Session writes must handle partial failure between Redis and PostgreSQL.

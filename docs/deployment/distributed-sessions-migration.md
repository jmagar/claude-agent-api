# Distributed Sessions Migration Checklist

## Pre-Deployment

- [ ] Verify Redis is running and accessible
- [ ] Verify PostgreSQL is running and accessible
- [ ] Run database migrations: `uv run alembic upgrade head`
- [ ] Verify Redis AOF persistence enabled: `redis-cli CONFIG GET appendonly`
- [ ] Backup existing Redis data: `redis-cli BGSAVE`
- [ ] Backup PostgreSQL database: `pg_dump claude_agent > backup.sql`

## Environment Variables

Ensure these are set:

```bash
REDIS_URL=redis://host:53380/0
REDIS_SESSION_TTL=7200
REDIS_INTERRUPT_CHANNEL=agent:interrupts
DATABASE_URL=postgresql+asyncpg://user:pass@host:53432/claude_agent
```

## Deployment Steps

1. **Deploy First Instance**
   ```bash
   docker-compose up -d api
   ```

2. **Verify Health**
   ```bash
   curl http://localhost:54000/api/v1/health
   ```

   Expected response:
   ```json
   {
     "status": "ok",
     "dependencies": {
       "postgres": {"status": "ok"},
       "redis": {"status": "ok"}
     }
   }
   ```

3. **Verify Session Creation**
   ```bash
   curl -X POST http://localhost:54000/api/v1/query \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test", "model": "sonnet"}'
   ```

   Check logs for:
   - "Session created in database"
   - "Session cached in Redis"
   - "Registered active session" (storage=redis)

4. **Deploy Second Instance** (Horizontal Scaling Test)
   ```bash
   # Modify docker-compose to add api2 service
   docker-compose up -d api2
   ```

5. **Verify Multi-Instance Operation**
   - Create session via instance 1
   - Retrieve session via instance 2
   - Interrupt session via instance 2
   - Verify instance 1 detects interrupt

## Post-Deployment Verification

- [ ] Check Redis keys: `redis-cli KEYS "active_session:*"`
- [ ] Check PostgreSQL sessions: `SELECT COUNT(*) FROM sessions;`
- [ ] Monitor cache hit rate: Check application logs for cache hits/misses
- [ ] Test Redis failover: Restart Redis, verify sessions recovered from PostgreSQL
- [ ] Test load balancing: Send requests to both instances, verify session state consistency

## Rollback Plan

If issues occur:

1. **Stop all API instances**
   ```bash
   docker-compose down api
   ```

2. **Restore previous version**
   ```bash
   git checkout <previous-commit>
   docker-compose up -d api
   ```

3. **Restore Redis data** (if needed)
   ```bash
   redis-cli FLUSHDB
   redis-cli < backup.rdb
   ```

4. **Restore PostgreSQL** (if needed)
   ```bash
   psql claude_agent < backup.sql
   ```

## Monitoring

After deployment, monitor:

- **Cache Performance**
  - Log messages: "Session retrieved from cache" vs "Session cache miss"
  - Target: >90% cache hit rate

- **Database Load**
  - PostgreSQL query count should be low (cache working)
  - Watch for "Failed to retrieve session from database" errors

- **Distributed Operations**
  - Log messages: "Registered active session" (storage=redis, distributed=true)
  - Log messages: "Interrupt signal sent" (distributed=true)

- **Lock Contention**
  - Watch for "Failed to acquire session lock" warnings
  - Should be rare (<0.1% of operations)

## Success Criteria

- ✅ Multiple API instances running simultaneously
- ✅ Sessions visible across all instances
- ✅ Interrupts work across instances
- ✅ Sessions survive Redis restart
- ✅ Cache hit rate >90%
- ✅ No lock timeout errors
- ✅ P0-1 resolved: Horizontal scaling enabled
- ✅ P0-2 resolved: Data durability guaranteed

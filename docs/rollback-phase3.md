# Phase 3 Rollback Emergency Procedure

**WARNING:** This is a LOSSY rollback. Original plaintext API keys cannot be recovered from SHA-256 hashes.

## When to Use This Procedure

Only use this if:
- Phase 3 migration causes critical production failure
- No other recovery option is available
- You accept that all API keys will be lost

**Effect:** All clients must regenerate API keys after rollback.

## Rollback Steps

### Step 1: Create Database Backup (Critical)

```bash
# Backup current state before rollback
pg_dump -h localhost -p 54432 -U postgres -d claude_agent_api \
  -F c -f backup_before_rollback_$(date +%Y%m%d_%H%M%S).dump
```

### Step 2: Run Alembic Downgrade

```bash
# Downgrade to Phase 2 (before plaintext columns were dropped)
uv run alembic downgrade 20260201_000006
```

**Effect:**
- Recreates `owner_api_key` column (but all values will be NULL)
- Recreates indexes on NULL column (not useful)
- Ownership information is preserved in `owner_api_key_hash`

### Step 3: Restore Phase 2 Application Code

```bash
# Checkout code from before Phase 3 changes
git revert <phase-3-commit-hash>

# Or checkout specific Phase 2 commit
git checkout <phase-2-commit-hash>

# Restart services
docker compose restart api
```

### Step 4: Generate New API Keys for All Clients

**Manual Process Required:**

1. Identify all client API keys from `owner_api_key_hash` values
2. Generate new API keys for each unique hash
3. Update `owner_api_key` column with new plaintext keys
4. Notify clients of new API keys
5. Update client configurations

**SQL to Generate New Keys:**

```sql
-- Generate UUIDs as new API keys
UPDATE sessions
SET owner_api_key = gen_random_uuid()::text
WHERE owner_api_key_hash IS NOT NULL;

UPDATE assistants
SET owner_api_key = gen_random_uuid()::text
WHERE owner_api_key_hash IS NOT NULL;
```

### Step 5: Communicate with Clients

**Email Template:**

```
Subject: URGENT: API Key Rotation Required

Due to an emergency database rollback, all API keys have been reset.

Your new API key: <new-key-here>

Please update your configuration immediately.

We apologize for the inconvenience.
```

### Step 6: Verify System Recovery

```bash
# Test authentication with new keys
curl -H "X-API-Key: <new-key>" http://localhost:54000/api/v1/sessions

# Check logs for successful authentication
docker compose logs api | grep "ownership_check"
```

## Prevention

**To avoid needing this rollback:**
- Thoroughly test Phase 3 in staging environment
- Verify hash consistency before Phase 3
- Monitor authentication logs during Phase 3 rollout
- Have database backups before Phase 3

## Post-Rollback Actions

1. **Root Cause Analysis:** Identify why Phase 3 failed
2. **Fix Issues:** Address problems before attempting Phase 3 again
3. **Extended Testing:** Test fix in staging for 2+ weeks
4. **Gradual Rollout:** Deploy Phase 3 to small percentage of traffic first
5. **Monitoring:** Enhanced monitoring for authentication failures

## Support

If you need assistance with this rollback:
- Check `#oncall-engineering` Slack channel
- Page on-call engineer via PagerDuty
- Escalate to CTO if critical production impact

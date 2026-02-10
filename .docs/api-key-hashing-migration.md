# API Key Hashing Migration Guide

**Security Fix:** Convert plaintext API key storage to secure SHA-256 hashing.

**Issue:** API keys were stored in plaintext in PostgreSQL (`owner_api_key` column in `sessions` and `assistants` tables).

**Solution:** Hash all API keys using SHA-256 before storage, use constant-time comparison for verification.

---

## ⚠️ CRITICAL DEPLOYMENT NOTES

**Current Branch Status:**
- ✅ **Phase 1 Migration EXISTS:** `20260201_000006_hash_api_keys.py`
- ✅ **Phase 2 Code EXISTS:** Application code uses hash-based authentication
- ✅ **Phase 3 Migration EXISTS:** `20260208_000007_drop_plaintext_api_keys.py`
- ✅ **Phase 3 Code EXISTS:** Models and services use only `owner_api_key_hash`

**Deployment Order:**
1. Run Phase 1 migration (adds hash columns, hashes existing keys)
2. Verify hash consistency: `uv run python scripts/verify_hash_consistency.py`
3. Deploy Phase 2 code (dual-column support, hash-based authentication)
4. Run Phase 2 in production for at least 7 days to verify stability
5. Verify hash consistency again before Phase 3
6. Run Phase 3 migration (drops plaintext columns)
7. Deploy Phase 3 code (uses only `owner_api_key_hash`)

**WARNING:** This branch contains Phase 3 code which uses ONLY `owner_api_key_hash`. The plaintext `owner_api_key` column must be dropped (Phase 3 migration) before deploying this code, otherwise the application will fail to start due to missing column references.

---

## Migration Strategy

This migration uses a **three-phase approach** to ensure zero downtime and safe rollback capability.

### Phase 1: Add Hash Column (Dual-Column Support)

**Migration:** `20260201_000006_hash_api_keys.py`

**Actions:**
1. Add `owner_api_key_hash` column to `sessions` and `assistants` tables
2. Hash all existing `owner_api_key` values into `owner_api_key_hash`
3. Keep both columns temporarily (allows rollback if needed)
4. Create indexes on `owner_api_key_hash` for efficient lookups

**Run:**
```bash
uv run alembic upgrade 20260201_000006
```

**State After Phase 1:**
- Both `owner_api_key` (plaintext) and `owner_api_key_hash` (SHA-256) columns exist
- All existing keys are hashed
- Application still uses plaintext column (not yet updated)

**Verification:**
```bash
# Verify hash consistency after migration
export DATABASE_URL="postgresql://..."
uv run python scripts/verify_hash_consistency.py
```

### Phase 2: Deploy Application Code

**Changes:**
1. Update `SessionRepository.create()` to write both columns
2. Update `SessionRepository.list_sessions()` to filter by hash
3. Update `SessionService` to use hashed keys in cache
4. Update middleware to compare hashed keys

**Deploy:**
```bash
# 1. Pull latest code
git pull origin main

# 2. Restart API server
docker compose restart api
```

**Verification:**
```bash
# Test authentication works
curl -H "X-API-Key: your-test-key" http://localhost:54000/api/v1/sessions

# Check logs for hash-based authentication
docker compose logs api | grep "owner_api_key_hash"
```

**State After Phase 2:**
- Application reads/writes both columns
- Authentication uses hashed comparison
- Backward compatible (can roll back to Phase 1)

**Verification:**
```bash
# Verify hash consistency before Phase 3
export DATABASE_URL="postgresql://..."
uv run python scripts/verify_hash_consistency.py
```

### Phase 3: Drop Plaintext Column (IMPLEMENTED)

⚠️ **WARNING:** This phase is IRREVERSIBLE. Only run after Phase 2 is verified.

**Status:** ✅ Migration and code changes implemented.

**Migration:** `20260208_000007_drop_plaintext_api_keys.py`

**Code Changes:**
- Removed `owner_api_key` column from `Session` and `Assistant` models
- Updated `SessionRepository.create()` to only set hash
- Updated `SessionService._enforce_owner()` to use only hash
- Updated `AssistantService` dataclass, cache, and ownership check
- All services and adapters use `owner_api_key_hash` exclusively

**Run Migration:**
```bash
# 1. Verify Phase 2 has been running successfully
export DATABASE_URL="postgresql://..."
uv run python scripts/verify_hash_consistency.py
# Must exit with code 0 (all hashes match)

# 2. Run the migration
uv run alembic upgrade 20260208_000007
```

**State After Phase 3:**
- Only `owner_api_key_hash` column remains
- Plaintext keys permanently removed
- Cannot roll back to plaintext storage

## Rollback Procedures

### Rollback from Phase 2 to Phase 1

If application code has issues after Phase 2 deployment:

```bash
# 1. Revert to previous code version
git checkout <previous-commit>

# 2. Restart API server
docker compose restart api
```

**Safe because:**
- Database still has both columns
- Old code uses `owner_api_key` (plaintext)
- No data loss

### Rollback from Phase 3 to Phase 2

⚠️ **WARNING:** This is a LOSSY rollback. Original API keys cannot be recovered from hashes.

```bash
# Downgrade migration (re-creates plaintext column as NULL)
uv run alembic downgrade 20260201_000006
```

**Effect:**
- `owner_api_key` column is re-created but all values are NULL
- `owner_api_key_hash` column is kept
- **All API keys must be manually regenerated**
- Clients will receive 401 Unauthorized until keys are updated

## Security Benefits

### Before (Plaintext Storage)

```sql
-- Attacker with DB access sees plaintext keys
SELECT owner_api_key FROM sessions;
-- Result: "sk-abc123", "sk-xyz789", ...
```

**Risks:**
- Database dumps expose API keys
- SQL injection can leak keys
- Insider threats have direct access
- Backup files contain plaintext keys

### After (Hashed Storage)

```sql
-- Attacker with DB access sees only hashes
SELECT owner_api_key_hash FROM sessions;
-- Result: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", ...
```

**Benefits:**
- API keys irreversible from hash (one-way function)
- Constant-time comparison prevents timing attacks
- Compliance with security best practices (OWASP)
- Reduced exposure risk (hashes cannot authenticate directly)

## Implementation Details

### Hash Function

```python
import hashlib

def hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()
```

**Properties:**
- **Deterministic:** Same key → same hash
- **One-way:** Cannot recover key from hash
- **Collision-resistant:** Different keys → different hashes
- **Avalanche effect:** 1-bit change → ~50% output bits change

### Verification

```python
import secrets

def verify_api_key(api_key: str, hashed: str) -> bool:
    """Verify API key against hash in constant time."""
    return secrets.compare_digest(hash_api_key(api_key), hashed)
```

**Security:**
- Uses `secrets.compare_digest()` for constant-time comparison
- Prevents timing side-channel attacks
- Attacker cannot infer hash by measuring response times

### Database Migration (PostgreSQL)

```sql
-- Add hash column
ALTER TABLE sessions ADD COLUMN owner_api_key_hash VARCHAR(64);

-- Hash existing keys using pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

UPDATE sessions
SET owner_api_key_hash = encode(digest(owner_api_key, 'sha256'), 'hex')
WHERE owner_api_key IS NOT NULL;

-- Create index for efficient lookups
CREATE INDEX idx_sessions_owner_api_key_hash ON sessions(owner_api_key_hash);
```

## Testing

### Run Crypto Tests

```bash
# Test hash and verification functions
uv run pytest tests/unit/utils/test_crypto.py -v

# Verify all security properties
uv run pytest tests/unit/utils/test_crypto.py::TestSecurityProperties -v
```

### Manual Verification

```python
from apps.api.utils.crypto import hash_api_key, verify_api_key

# Hash an API key
api_key = "test-key-12345"
hashed = hash_api_key(api_key)
print(f"Hash: {hashed}")
# Output: Hash: a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3

# Verify correct key
assert verify_api_key("test-key-12345", hashed) is True

# Verify wrong key
assert verify_api_key("wrong-key", hashed) is False
```

## Production Deployment Checklist

### Pre-Deployment

- [ ] Run all tests: `uv run pytest tests/unit/utils/test_crypto.py`
- [ ] Backup database: `pg_dump claude_agent > backup.sql`
- [ ] Test migration on staging environment
- [ ] Verify rollback procedure works
- [ ] Document current API keys for regeneration if needed

### Phase 1 Deployment

- [ ] Run migration: `uv run alembic upgrade 20260201_000006`
- [ ] Verify hash column populated: `SELECT COUNT(*) FROM sessions WHERE owner_api_key_hash IS NOT NULL`
- [ ] Check migration logs for errors
- [ ] Verify indexes created: `\d sessions` in psql
- [ ] **Run hash consistency verification:** `uv run python scripts/verify_hash_consistency.py`

### Phase 2 Deployment

- [ ] Deploy application code with hash support
- [ ] Restart API server
- [ ] Test authentication with existing API keys
- [ ] Monitor logs for hash-based authentication
- [ ] Verify no 401 errors from legitimate clients
- [ ] Run integration tests: `uv run pytest tests/integration/`

### Phase 3 Deployment (Optional)

⚠️ **Only after Phase 2 runs successfully in production for at least 7 days**

- [ ] Verify no rollback needed
- [ ] Confirm all clients authenticated successfully
- [ ] **MANDATORY: Run hash consistency verification:** `uv run python scripts/verify_hash_consistency.py` (must exit code 0)
- [ ] Take final backup before irreversible change
- [ ] Run migration: `uv run alembic upgrade 20260201_000007`
- [ ] Verify plaintext column dropped: `\d sessions` in psql
- [ ] Document that rollback requires API key regeneration

## Monitoring

### Health Checks

```bash
# Check authentication works
curl -H "X-API-Key: test-key" http://localhost:54000/api/v1/health

# Check session creation with API key
curl -X POST http://localhost:54000/api/v1/sessions \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "sonnet"}'
```

### Database Queries

```sql
-- Count sessions with hashed keys
SELECT COUNT(*) FROM sessions WHERE owner_api_key_hash IS NOT NULL;

-- Verify no plaintext keys after Phase 3
SELECT COUNT(*) FROM sessions WHERE owner_api_key IS NOT NULL;
-- Should be 0 after Phase 3

-- Check hash distribution (should be unique)
SELECT COUNT(DISTINCT owner_api_key_hash) FROM sessions;
```

## Troubleshooting

### Issue: Hash consistency verification fails

**Symptom:** `verify_hash_consistency.py` exits with code 1 and reports mismatches.

**Cause:** Database corruption or incomplete migration from Phase 1.

**Solution:**
```bash
# 1. Review mismatch details from script output
uv run python scripts/verify_hash_consistency.py

# 2. Re-run Phase 1 migration to recompute all hashes
uv run alembic downgrade 20260201_000005  # One revision before hash migration
uv run alembic upgrade 20260201_000006    # Re-apply hash migration

# 3. Verify hashes now match
uv run python scripts/verify_hash_consistency.py
# Must exit code 0 before proceeding

# 4. If mismatches persist, check for application bugs writing incorrect hashes
docker compose logs api | grep "owner_api_key_hash"
```

**Prevention:**
- Always run verification script after Phase 1 and before Phase 3
- Monitor application logs during Phase 2 for hash computation errors
- Use staging environment to test migration before production

### Issue: Authentication fails after Phase 2

**Symptom:** Clients receive 401 Unauthorized with valid API keys.

**Cause:** Hash mismatch between stored hash and computed hash.

**Solution:**
```bash
# Check if hash column is populated
psql -c "SELECT owner_api_key_hash FROM sessions LIMIT 5;"

# Verify hash computation matches PostgreSQL
python3 << EOF
from apps.api.utils.crypto import hash_api_key
import subprocess

key = "test-key"
py_hash = hash_api_key(key)
pg_hash = subprocess.check_output([
    "psql", "-t", "-c",
    f"SELECT encode(digest('{key}', 'sha256'), 'hex');"
]).decode().strip()

print(f"Python: {py_hash}")
print(f"PostgreSQL: {pg_hash}")
assert py_hash == pg_hash
EOF
```

### Issue: Migration fails with "column already exists"

**Symptom:** Alembic migration fails with duplicate column error.

**Cause:** Migration was partially applied.

**Solution:**
```bash
# Check current migration state
uv run alembic current

# Check if column exists
psql -c "\d sessions" | grep owner_api_key_hash

# If column exists but migration not recorded:
uv run alembic stamp 20260201_000006
```

### Issue: Performance degradation after migration

**Symptom:** Slow session queries after Phase 2.

**Cause:** Missing index on `owner_api_key_hash`.

**Solution:**
```sql
-- Verify index exists
SELECT indexname FROM pg_indexes WHERE tablename = 'sessions';

-- Recreate index if missing
CREATE INDEX CONCURRENTLY idx_sessions_owner_api_key_hash
ON sessions(owner_api_key_hash);
```

## FAQ

**Q: Why SHA-256 instead of bcrypt/scrypt/Argon2?**

A: API keys are high-entropy random strings (not user passwords). They don't need slow key derivation functions designed to resist dictionary attacks. SHA-256 provides sufficient security with better performance.

**Q: Can we recover original API keys from hashes?**

A: No. SHA-256 is a one-way cryptographic hash function. Original keys cannot be recovered. This is a security feature, not a limitation.

**Q: What if we need to migrate to a different hash algorithm?**

A: Add a new column (e.g., `owner_api_key_hash_v2`) and repeat the migration process. Keep old column until all keys are re-hashed.

**Q: How does this affect API key rotation?**

A: API key rotation remains the same. When a client rotates their key, the new key is hashed and stored. Old hash is deleted.

**Q: Is the hash visible in logs?**

A: Yes, but hashes are not sensitive. They cannot be used to authenticate without knowing the original key. Logs can safely contain hashes for debugging.

**Q: What about API keys in Redis cache?**

A: Cache stores hashed keys (same as database). Cache-aside pattern ensures consistency between Redis and PostgreSQL.

## References

- [OWASP: Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)
- [PostgreSQL pgcrypto extension](https://www.postgresql.org/docs/current/pgcrypto.html)
- [SHA-256 specification (FIPS 180-4)](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-01 | 1.0 | Claude | Initial migration guide |
| 2026-02-02 | 2.0 | Claude | Phase 3 implementation complete - migration + code changes |

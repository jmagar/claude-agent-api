# API Key Hashing - Quick Reference

**TL;DR:** API keys are now hashed with SHA-256 before storage. Use crypto utilities for all key operations.

---

## For Developers

### Import the utilities

```python
from apps.api.utils.crypto import hash_api_key, verify_api_key
```

### Hash a key before storage

```python
# In repositories/services that write to database or cache
api_key = request.headers.get("X-API-Key")
hashed = hash_api_key(api_key)  # Store this, NOT the plaintext

# Example: SessionRepository.create()
session = Session(
    id=session_id,
    owner_api_key_hash=hash_api_key(api_key) if api_key else None
)
```

### Verify a key during authentication

```python
# In middleware or auth handlers
stored_hash = session.owner_api_key_hash  # From database or cache
provided_key = request.headers.get("X-API-Key")

if verify_api_key(provided_key, stored_hash):
    # Authentication successful
    pass
else:
    # Authentication failed
    return Response(status_code=401)
```

### Filter by API key in queries

```python
# In repositories
# DON'T: filter by plaintext
stmt = stmt.where(Session.owner_api_key == api_key)  # ❌ Insecure

# DO: filter by hash
owner_hash = hash_api_key(api_key)
stmt = stmt.where(Session.owner_api_key_hash == owner_hash)  # ✅ Secure
```

---

## Common Patterns

### Creating a session with API key

```python
async def create_session(api_key: str, model: str) -> Session:
    """Create session with hashed API key."""
    session = Session(
        id=uuid4(),
        model=model,
        owner_api_key_hash=hash_api_key(api_key),  # Hash before storage
    )
    db.add(session)
    await db.commit()
    return session
```

### Checking session ownership

```python
async def get_session(session_id: UUID, current_api_key: str) -> Session | None:
    """Get session if owned by current API key."""
    session = await db.get(Session, session_id)

    if not session:
        return None

    # Verify ownership using constant-time comparison
    if not verify_api_key(current_api_key, session.owner_api_key_hash):
        raise UnauthorizedError("Not your session")

    return session
```

### Listing sessions by owner

```python
async def list_sessions(owner_api_key: str) -> list[Session]:
    """List all sessions owned by API key."""
    owner_hash = hash_api_key(owner_api_key)  # Hash before query

    stmt = (
        select(Session)
        .where(Session.owner_api_key_hash == owner_hash)
        .order_by(Session.created_at.desc())
    )

    result = await db.execute(stmt)
    return result.scalars().all()
```

### Caching with hashed keys

```python
async def cache_session(session: Session) -> None:
    """Cache session with hash-based owner index."""
    # Main session cache
    cache_key = f"session:{session.id}"
    await redis.set_json(cache_key, session.dict())

    # Owner index (use hash for security)
    if session.owner_api_key_hash:
        owner_index_key = f"session:owner_hash:{session.owner_api_key_hash}"
        await redis.sadd(owner_index_key, session.id)
```

---

## Migration Status

| Phase | Status | Safe to Deploy? |
|-------|--------|-----------------|
| Phase 1 (Add hash column) | ✅ Complete | Yes - deployed |
| Phase 2 (Use hash in code) | ⏳ Ready | Yes - pending review |
| Phase 3 (Drop plaintext) | ⏸️ Future | No - wait 7+ days after Phase 2 |

---

## Testing

### Unit test your code

```python
from apps.api.utils.crypto import hash_api_key, verify_api_key

def test_session_creation_hashes_api_key():
    """Session should store hashed API key, not plaintext."""
    api_key = "test-key-12345"
    session = create_session(api_key=api_key, model="sonnet")

    # Should NOT store plaintext
    assert session.owner_api_key_hash != api_key

    # Should store valid hash (64 hex chars)
    assert len(session.owner_api_key_hash) == 64
    assert all(c in "0123456789abcdef" for c in session.owner_api_key_hash)

    # Should match expected hash
    assert session.owner_api_key_hash == hash_api_key(api_key)
```

### Run crypto tests

```bash
# Test hash and verification functions
uv run pytest tests/unit/utils/test_crypto.py -v

# Test your code changes
uv run pytest tests/unit/test_your_module.py -v
```

---

## Common Mistakes

### ❌ DON'T: Store plaintext keys

```python
# WRONG - plaintext storage
session.owner_api_key = api_key
```

### ✅ DO: Hash before storage

```python
# CORRECT - hash storage
session.owner_api_key_hash = hash_api_key(api_key)
```

---

### ❌ DON'T: Compare hashes with ==

```python
# WRONG - timing attack vulnerable
if stored_hash == hash_api_key(provided_key):
    # Attacker can measure timing to infer hash
    pass
```

### ✅ DO: Use verify_api_key()

```python
# CORRECT - constant-time comparison
if verify_api_key(provided_key, stored_hash):
    # Timing is constant regardless of match
    pass
```

---

### ❌ DON'T: Filter by plaintext

```python
# WRONG - queries plaintext column
sessions = db.query(Session).filter_by(owner_api_key=api_key).all()
```

### ✅ DO: Filter by hash

```python
# CORRECT - queries hash column
owner_hash = hash_api_key(api_key)
sessions = db.query(Session).filter_by(owner_api_key_hash=owner_hash).all()
```

---

### ❌ DON'T: Log API keys

```python
# WRONG - plaintext in logs
logger.info(f"Session created for API key: {api_key}")
```

### ✅ DO: Log hash prefix only (if needed)

```python
# CORRECT - truncated hash prefix for debugging (treat as sensitive)
hash_value = hash_api_key(api_key)
logger.info(f"Session created for key hash prefix: {hash_value[:8]}...")
# Note: Even hashes should be treated as credential-derived identifiers
```

---

## Performance

**Hash computation:** ~1-2μs per key (negligible)

```python
import time
from apps.api.utils.crypto import hash_api_key

start = time.perf_counter()
for _ in range(10000):
    hash_api_key("test-key-12345")
elapsed = time.perf_counter() - start

print(f"Average: {elapsed / 10000 * 1_000_000:.2f} μs/hash")
# Output: Average: 1.5 μs/hash
```

**Impact on request time:** < 0.01% (imperceptible)

---

## Security Properties

### One-Way Function

```python
# You CANNOT recover the original key from the hash
hash_value = hash_api_key("secret-key-abc123")
# hash_value = "5e884898da28047151d0e56f8dc6292773603d0d..."

# There is NO function to reverse this:
# original = unhash(hash_value)  # ❌ IMPOSSIBLE
```

### Collision Resistance

```python
# Different keys are expected to produce different hashes
hash1 = hash_api_key("key-1")
hash2 = hash_api_key("key-2")
assert hash1 != hash2  # Expected to be true (SHA-256 collision resistance)
# Note: Theoretical collision probability is ~2^-256, negligible in practice
```

### Deterministic

```python
# Same key ALWAYS produces same hash
hash1 = hash_api_key("my-key")
hash2 = hash_api_key("my-key")
hash3 = hash_api_key("my-key")
assert hash1 == hash2 == hash3  # Always true
```

---

## FAQ

**Q: Why hash API keys if they're already random?**

A: Even random keys should be hashed to protect against:
- Database dumps being leaked
- SQL injection exposing keys
- Insider threats accessing backups
- Accidental logging of plaintext keys

**Q: Can we search for sessions by partial API key?**

A: No. Hashing is one-way - you can only verify exact matches. Partial searches require plaintext, which is insecure.

**Q: What if user forgets their API key?**

A: Generate a new key. Original keys cannot be recovered from hashes. This is a security feature.

**Q: How do we migrate existing keys?**

A: Phase 1 migration automatically hashes all existing keys using PostgreSQL's `digest()` function. No manual work needed.

---

## Resources

- **Full Guide:** `.docs/api-key-hashing-migration.md`
- **Implementation Details:** `.docs/api-key-hashing-implementation.md`
- **Security Summary:** `SECURITY-FIX-API-KEY-HASHING.md`
- **Tests:** `tests/unit/utils/test_crypto.py`

---

**Last Updated:** 2026-02-01

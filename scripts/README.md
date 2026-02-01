# Scripts

Utility scripts for maintenance, verification, and deployment tasks.

## Hash Consistency Verification

### verify_hash_consistency.py

Verifies that all `owner_api_key_hash` values in the database correctly match the SHA-256 hash of their corresponding `owner_api_key` plaintext values.

**Purpose:**
During the phased migration to hashed API keys (Issues #1-#7), we temporarily maintain both plaintext (`owner_api_key`) and hashed (`owner_api_key_hash`) columns. This script detects data corruption or inconsistencies before Phase 3, which will drop the plaintext column permanently.

**When to Run:**
- After Phase 1 (migration adds hash column) - baseline verification
- After Phase 2 (app uses hashes) - verify no corruption during transition
- **Before Phase 3 (drop plaintext column) - MANDATORY pre-deployment check**
- Periodically during Phase 2 as a health check

**What It Checks:**
For each record with `owner_api_key` NOT NULL:
1. Computes SHA-256 hash of `owner_api_key` (plaintext)
2. Compares with `owner_api_key_hash` (stored hash)
3. Reports any mismatches as data corruption

**Exit Codes:**
- `0` - All hashes match (safe to proceed with Phase 3)
- `1` - Mismatches found (DO NOT DEPLOY PHASE 3)

**Usage:**
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:pass@localhost:54432/dbname"

# Run verification
uv run python scripts/verify_hash_consistency.py

# Or inline:
DATABASE_URL="postgresql://..." uv run python scripts/verify_hash_consistency.py
```

**Example Output (Success):**
```
Connecting to database: localhost:54432/claude_agent

[1/2] Verifying sessions table...
  Total records checked: 1523
  Records with matching hashes: 1523
  Records with mismatches: 0

[2/2] Verifying assistants table...
  Total records checked: 42
  Records with matching hashes: 42
  Records with mismatches: 0

======================================================================
SUMMARY
======================================================================
Total records checked: 1565
Records with matching hashes: 1565
Records with mismatches: 0

✅ VERIFICATION PASSED - ALL HASHES MATCH
Database is consistent and ready for Phase 3 deployment.
```

**Example Output (Failure):**
```
Connecting to database: localhost:54432/claude_agent

[1/2] Verifying sessions table...
  Total records checked: 1523
  Records with matching hashes: 1523
  Records with mismatches: 0

[2/2] Verifying assistants table...
  Total records checked: 42
  Records with matching hashes: 41
  Records with mismatches: 1

  MISMATCHES FOUND:
  assistants.id=asst_abc123: stored=wrong_hash, computed=correct_hash

======================================================================
SUMMARY
======================================================================
Total records checked: 1565
Records with matching hashes: 1564
Records with mismatches: 1

❌ VERIFICATION FAILED - DATA CORRUPTION DETECTED
Found 1 hash mismatch(es) across tables.

ACTION REQUIRED:
1. DO NOT PROCEED with Phase 3 deployment (dropping plaintext column)
2. Investigate root cause of hash mismatches
3. Run Phase 1 migration again to recompute hashes
4. Re-run this script to verify fixes
```

**Implementation:**
- Uses raw SQL with `encode(digest(owner_api_key, 'sha256'), 'hex')` to match database-side hash computation
- Compares stored hash with computed hash for every record
- Reports record IDs, stored hash, and computed hash for mismatches
- Zero tolerance for hash mismatches (any mismatch = deployment blocked)

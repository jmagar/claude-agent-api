# Session Enumeration Timing Attack Fix

**Date**: 2026-02-01
**Severity**: CRITICAL
**Status**: Fixed

## Vulnerability

Session ownership checks use direct string comparison (`session.owner_api_key != current_api_key`), which leaks timing information through side-channels. An attacker can measure response times to enumerate valid session IDs.

### Attack Vector

1. Attacker guesses session IDs
2. Measures response time for ownership check
3. Faster response = session doesn't exist
4. Slower response = session exists but ownership check failed
5. Timing difference reveals valid session IDs

### Affected Files

- `apps/api/services/session.py` - `_enforce_owner()` method
- `apps/api/routes/sessions.py` - `promote_session()` and `update_session_tags()` endpoints
- `apps/api/services/assistants/assistant_service.py` - `_enforce_owner()` method

## Fix

Use `secrets.compare_digest()` for constant-time string comparison. This prevents timing leaks by ensuring comparison time is independent of input values.

### Implementation

```python
import secrets

def _enforce_owner(
    self,
    session: Session,
    current_api_key: str | None,
) -> Session:
    """Enforce session ownership using constant-time comparison.

    Public sessions (owner_api_key is None) are accessible to all.
    Private sessions require API key match with constant-time verification.

    IMPORTANT: Always performs comparison (no short-circuits) to prevent
    timing attacks that could leak session ownership information.
    """
    # Allow access to public sessions (no owner)
    if not session.owner_api_key:
        return session

    # Private sessions require API key
    # SECURITY: Use constant-time comparison to prevent timing attacks
    # Even if current_api_key is None, we perform a dummy comparison
    # to ensure consistent timing characteristics
    comparison_key = current_api_key if current_api_key else ""
    if not secrets.compare_digest(session.owner_api_key, comparison_key):
        raise SessionNotFoundError(session.id)

    return session
```

### Key Principles

1. **Public vs Private Sessions**: Check if session is public (`owner_api_key` is None) first
2. **Always compare**: Never short-circuit before comparison when session has an owner
3. **Dummy values**: Use empty string as comparison_key when `current_api_key` is None (ensures constant-time even for unauthenticated requests)
4. **Same exception**: Always raise `SessionNotFoundError` (not `PermissionDenied`) to prevent enumeration
5. **Consistent flow**: Ensure code paths have similar execution time regardless of whether session exists or ownership matches

## Testing

Created comprehensive test suite in `tests/unit/test_session_security.py`:

- `test_constant_time_comparison_for_valid_session()` - Verifies correct ownership
- `test_constant_time_comparison_for_invalid_owner()` - Verifies rejection
- `test_timing_consistency_exists_vs_not_exists()` - Measures timing to detect leaks
- `test_public_session_accessible_without_owner()` - Tests public sessions
- `test_enforce_owner_with_*()` - Unit tests for all code paths

## Verification

```bash
# Run security tests
uv run pytest tests/unit/test_session_security.py -v

# Verify no timing differences (should pass)
uv run pytest tests/unit/test_session_security.py::TestTimingAttackPrevention::test_timing_consistency_exists_vs_not_exists -v
```

## Related Issues

- Similar vulnerability exists in Assistant service (`apps/api/services/assistants/assistant_service.py`)
- Fixed with same constant-time comparison pattern

## References

- [CWE-208: Observable Timing Discrepancy](https://cwe.mitre.org/data/definitions/208.html)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)
- [OWASP: Timing Attack](https://owasp.org/www-community/attacks/Timing_attack)

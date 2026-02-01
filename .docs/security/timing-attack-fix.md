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
    """Enforce session ownership using constant-time comparison."""
    if not current_api_key:
        return session  # No API key = allow access

    # SECURITY: Always perform comparison to prevent timing leaks
    if session.owner_api_key is None:
        # Compare against dummy value to ensure constant execution time
        dummy_key = "x" * max(len(current_api_key), 32)
        secrets.compare_digest(current_api_key, dummy_key)
        return session  # Public session

    # Constant-time comparison
    keys_match = secrets.compare_digest(session.owner_api_key, current_api_key)
    if not keys_match:
        raise SessionNotFoundError(session.id)

    return session
```

### Key Principles

1. **Always compare**: Never short-circuit before comparison
2. **Dummy values**: Compare against dummy when `owner_api_key` is None
3. **Same exception**: Always raise `SessionNotFoundError` (not `PermissionDenied`) to prevent enumeration
4. **Consistent flow**: Ensure code paths have similar execution time

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

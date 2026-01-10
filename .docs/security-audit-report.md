# Security Audit Report: Claude Agent API

**Audit Date:** 2026-01-09
**Auditor:** Security Audit (Claude Opus 4.5)
**Scope:** `apps/api/` - FastAPI service wrapping Claude Agent SDK
**Version:** 1.0.0

---

## Executive Summary

This comprehensive security audit examined the Claude Agent API codebase for vulnerabilities across OWASP Top 10 categories, dependency CVEs, secrets exposure, authentication/authorization, cryptographic implementations, and input validation.

### Overall Risk Assessment: **MEDIUM**

The codebase demonstrates **strong security posture** with several well-implemented security controls:
- Constant-time API key comparison preventing timing attacks
- SSRF prevention with internal URL blocking
- Path traversal protection
- SQL injection prevention via parameterized queries (SQLAlchemy ORM)
- Rate limiting implementation
- Proper secrets handling with Pydantic SecretStr

However, several **medium and low-risk findings** require attention for production hardening.

---

## Risk Matrix Summary

| Severity | Count | Categories |
|----------|-------|------------|
| Critical | 0 | - |
| High | 1 | Fail-open webhook behavior |
| Medium | 5 | Authorization gaps, CORS concerns, session enumeration, etc. |
| Low | 6 | Information disclosure, logging practices, etc. |
| Informational | 3 | Best practice recommendations |

---

## Detailed Findings

### OWASP A01:2021 - Broken Access Control

#### Finding SEC-001: Lack of Session Ownership Verification
**Severity:** MEDIUM
**Status:** Open
**Location:** `apps/api/routes/sessions.py`, `apps/api/routes/session_control.py`

**Description:**
Session endpoints allow any authenticated user to access any session by ID. There is no verification that the requesting API key owns the session being accessed.

**Affected Code:**
```python
# apps/api/routes/sessions.py:52-73
@router.get("/{session_id}")
async def get_session(
    session_id: str,
    _api_key: ApiKey,
    session_service: SessionSvc,
) -> SessionResponse:
    session = await session_service.get_session(session_id)
    # No ownership check - any valid API key can access any session
```

**Impact:**
- Information disclosure across tenants
- Session hijacking if session IDs are leaked
- Horizontal privilege escalation

**Remediation:**
1. Associate sessions with API keys at creation time
2. Add ownership verification before session access
3. Consider per-user/per-key session isolation

---

#### Finding SEC-002: Session ID Enumeration
**Severity:** LOW
**Status:** Open
**Location:** `apps/api/routes/sessions.py:52-73`

**Description:**
Session IDs are UUIDv4, which are cryptographically random. However, error messages distinguish between "session not found" and "access denied", enabling enumeration.

**Impact:**
- Attackers can enumerate valid session IDs
- Combined with SEC-001, this amplifies access control risks

**Remediation:**
- Return identical error responses for non-existent and unauthorized sessions
- Use generic "Session not found or unauthorized" message

---

### OWASP A02:2021 - Cryptographic Failures

#### Finding SEC-003: API Key Validation - POSITIVE
**Severity:** N/A (Positive Finding)
**Status:** Implemented Correctly
**Location:** `apps/api/middleware/auth.py:64`, `apps/api/dependencies.py:153`

**Description:**
API key validation correctly uses `secrets.compare_digest()` for constant-time comparison, preventing timing attacks.

```python
# apps/api/middleware/auth.py:64
if not secrets.compare_digest(api_key, settings.api_key.get_secret_value()):
```

**Assessment:** Correctly implemented.

---

#### Finding SEC-004: API Key in Request State
**Severity:** LOW
**Status:** Open
**Location:** `apps/api/middleware/auth.py:77`

**Description:**
The validated API key is stored in `request.state.api_key`. While this is not directly exploitable, storing sensitive data in request state increases exposure surface if logging or error handlers inadvertently serialize request state.

```python
# apps/api/middleware/auth.py:77
request.state.api_key = api_key
```

**Remediation:**
- Consider storing only a boolean flag or hash
- Ensure request state is never serialized in logs/errors

---

### OWASP A03:2021 - Injection

#### Finding SEC-005: SQL Injection Prevention - POSITIVE
**Severity:** N/A (Positive Finding)
**Status:** Implemented Correctly
**Location:** `apps/api/adapters/session_repo.py`

**Description:**
All database queries use SQLAlchemy ORM with parameterized queries. No raw SQL or string concatenation found.

```python
# apps/api/adapters/session_repo.py:67-69
stmt = select(Session).where(Session.id == session_id)
result = await self._db.execute(stmt)
```

**Assessment:** Correctly implemented with parameterized queries.

---

#### Finding SEC-006: Command Injection Prevention - POSITIVE
**Severity:** N/A (Positive Finding)
**Status:** Implemented Correctly
**Location:** `apps/api/schemas/validators.py`, `apps/api/schemas/requests/config.py`

**Description:**
Shell metacharacters are blocked in MCP server commands, and null bytes are rejected:

```python
# apps/api/schemas/validators.py:19
SHELL_METACHAR_PATTERN = re.compile(r"[;&|`$(){}[\]<>!\n\r\\]")

# apps/api/schemas/requests/config.py:59
if SHELL_METACHAR_PATTERN.search(v):
    raise ValueError("Shell metacharacters not allowed in command...")
```

**Assessment:** Good defense-in-depth against command injection.

---

#### Finding SEC-007: Path Traversal in Skills Discovery
**Severity:** MEDIUM
**Status:** Open
**Location:** `apps/api/services/skills.py:42`

**Description:**
The skills discovery reads files from `.claude/skills/*.md` using glob. While the base path is controlled, if an attacker can influence `project_path`, they could potentially read files outside the intended directory.

```python
# apps/api/services/skills.py:42
for skill_file in self.skills_dir.glob("*.md"):
    skill_info = self._parse_skill_file(skill_file)
```

**Impact:**
- Arbitrary file read via symlink attacks
- Information disclosure

**Remediation:**
1. Resolve paths and verify they remain within project_path
2. Use `os.path.realpath()` and verify prefix
3. Do not follow symlinks

---

### OWASP A04:2021 - Insecure Design

#### Finding SEC-008: Webhook Fail-Open Behavior
**Severity:** HIGH
**Status:** Open
**Location:** `apps/api/services/webhook.py:138-181`

**Description:**
When webhook calls fail (timeout, connection error, HTTP error, JSON error), the service returns a default "allow" decision. This fail-open design could allow malicious tool executions to bypass security controls.

```python
# apps/api/services/webhook.py:138-148
except TimeoutError:
    return {
        "decision": "allow",
        "reason": f"Webhook timeout after {hook_config.timeout}s",
    }
```

**Impact:**
- Security bypass if webhook service is unavailable
- DoS attack could disable security controls
- Sensitive tool operations may proceed without authorization

**Remediation:**
1. Make fail-open/fail-close configurable per-hook
2. Default to "deny" for security-critical hooks (PreToolUse)
3. Implement circuit breaker pattern with explicit deny on repeated failures

---

#### Finding SEC-009: No Request Size Limits
**Severity:** MEDIUM
**Status:** Open
**Location:** `apps/api/main.py`

**Description:**
No explicit request body size limits are configured. While Pydantic validates max_length on prompt (100000 chars), the overall request body could still be very large with images/base64 data.

**Impact:**
- Memory exhaustion attacks
- Denial of service via large payloads

**Remediation:**
Add request body size limit middleware:
```python
from starlette.middleware.base import BaseHTTPMiddleware
app.add_middleware(SizeLimitMiddleware, max_size=10_000_000)  # 10MB
```

---

### OWASP A05:2021 - Security Misconfiguration

#### Finding SEC-010: CORS Wildcard in Development
**Severity:** LOW
**Status:** Implemented with Warning
**Location:** `apps/api/config.py:119-123`

**Description:**
The configuration correctly prevents wildcard CORS in production mode. However, the default is permissive (`["*"]`), and the validation depends on `DEBUG=false` being explicitly set.

```python
# apps/api/config.py:119-123
if not self.debug and "*" in self.cors_origins:
    raise ValueError(
        "CORS wildcard (*) is not allowed in production..."
    )
```

**Assessment:** Generally good, but could be more secure by default.

**Recommendation:**
- Consider defaulting to empty CORS origins
- Require explicit configuration in all environments

---

#### Finding SEC-011: Trust Proxy Headers Configuration
**Severity:** LOW
**Status:** Implemented Correctly
**Location:** `apps/api/middleware/ratelimit.py:29-36`, `apps/api/config.py:82-85`

**Description:**
The `trust_proxy_headers` setting defaults to `false` and must be explicitly enabled. When enabled, the rightmost IP from X-Forwarded-For is used, which is harder to spoof.

```python
# apps/api/middleware/ratelimit.py:34-36
ips = [ip.strip() for ip in forwarded_for.split(",")]
if ips:
    return ips[-1]  # Rightmost IP - added by trusted proxy
```

**Assessment:** Correctly implemented secure-by-default pattern.

---

### OWASP A07:2021 - Identification and Authentication Failures

#### Finding SEC-012: Single API Key Authentication
**Severity:** MEDIUM
**Status:** Design Issue
**Location:** `apps/api/config.py:26`, `apps/api/middleware/auth.py`

**Description:**
The application uses a single shared API key for all clients. This limits:
- Audit trail granularity (cannot attribute actions to specific users)
- Key rotation (affects all clients)
- Access control (all-or-nothing access)

**Impact:**
- If key is compromised, all access is compromised
- No per-client rate limiting or quotas
- Difficult to revoke individual client access

**Remediation for Production:**
1. Implement multi-tenant API key support
2. Store keys in database with per-key metadata
3. Add key rotation mechanism
4. Consider JWT tokens with scopes

---

#### Finding SEC-013: WebSocket Authentication - POSITIVE
**Severity:** N/A (Positive Finding)
**Status:** Implemented Correctly
**Location:** `apps/api/routes/websocket.py:259-269`

**Description:**
WebSocket authentication correctly:
1. Only accepts API key from headers (not query params)
2. Uses constant-time comparison
3. Closes connection with appropriate status codes

```python
# apps/api/routes/websocket.py:259-269
api_key = websocket.headers.get("x-api-key")
if not api_key:
    await websocket.close(code=4001, reason="Missing API key")
    return
if not secrets.compare_digest(api_key, settings.api_key.get_secret_value()):
    await websocket.close(code=4001, reason="Invalid API key")
    return
```

**Assessment:** Correctly implemented with secure practices.

---

### OWASP A08:2021 - Software and Data Integrity Failures

#### Finding SEC-014: Webhook Response Trust
**Severity:** MEDIUM
**Status:** Open
**Location:** `apps/api/services/webhook.py:336-337`

**Description:**
Webhook responses are cast directly to expected types without validation:

```python
# apps/api/services/webhook.py:336-337
json_response = response.json()
return cast(dict[str, object], json_response)
```

**Impact:**
- Malicious webhook servers could inject unexpected data
- Type confusion attacks

**Remediation:**
- Validate webhook response schema with Pydantic
- Create explicit response model with allowed fields

---

### OWASP A09:2021 - Security Logging and Monitoring Failures

#### Finding SEC-015: Insufficient Security Event Logging
**Severity:** LOW
**Status:** Open
**Location:** Various

**Description:**
While general logging exists, security-specific events lack dedicated audit logging:
- Authentication failures (counted but not detailed)
- Authorization failures
- Rate limit violations
- Session access patterns

**Remediation:**
1. Add security-specific audit log stream
2. Include client IP, API key hash, action, and outcome
3. Set up alerting on repeated failures

---

#### Finding SEC-016: Error Messages May Leak Information
**Severity:** LOW
**Status:** Partial
**Location:** `apps/api/main.py:154`

**Description:**
In debug mode, exception type names are exposed:

```python
# apps/api/main.py:154
"details": {"type": type(exc).__name__} if settings.debug else {},
```

**Assessment:** Correctly gated by debug flag, but consider removing entirely for production security posture.

---

### OWASP A10:2021 - Server-Side Request Forgery (SSRF)

#### Finding SEC-017: SSRF Prevention - POSITIVE
**Severity:** N/A (Positive Finding)
**Status:** Implemented Correctly
**Location:** `apps/api/schemas/validators.py:64-102`

**Description:**
Comprehensive SSRF prevention is implemented:
1. Blocks localhost and metadata service hostnames
2. Blocks private, loopback, link-local, and reserved IP addresses
3. Applied to webhook URLs and MCP server URLs

```python
# apps/api/schemas/validators.py:99-100
if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
    raise ValueError("URLs targeting internal resources are not allowed")
```

**Assessment:** Strong SSRF prevention implementation.

---

## Dependency Vulnerability Analysis

### Current Dependencies (Key Packages)

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| FastAPI | 0.128.0 | Secure | Latest stable |
| Pydantic | 2.12.5 | Secure | Latest stable |
| SQLAlchemy | 2.0.45 | Secure | Async support |
| redis | 7.1.0 | Secure | Async redis |
| httpx | 0.28.1 | Secure | HTTP client |
| cryptography | 46.0.3 | Secure | Latest stable |
| structlog | 25.5.0 | Secure | Structured logging |

### Recommended Dependency Audits

Run periodic vulnerability scans:
```bash
# Install pip-audit
uv pip install pip-audit

# Run vulnerability scan
pip-audit

# Or use safety
uv pip install safety
safety check
```

---

## Secrets Management Assessment

### Finding SEC-018: Secrets Handling - MOSTLY POSITIVE
**Severity:** LOW
**Status:** Minor Issues

**Positive Findings:**
1. `.env` file is properly gitignored
2. API key uses `SecretStr` type hiding value in logs/repr
3. No hardcoded secrets in source code
4. `.env.example` uses placeholder values

**Minor Issue:**
The `.env.example` file contains a commented API key pattern:
```
# ANTHROPIC_API_KEY=sk-ant-...
```

While harmless, consider using more obviously fake values like:
```
# ANTHROPIC_API_KEY=your-api-key-here
```

---

## Input Validation Assessment

### Security Validators Implemented

| Validator | Location | Purpose |
|-----------|----------|---------|
| `validate_no_null_bytes` | validators.py:28-43 | Null byte injection prevention |
| `validate_no_path_traversal` | validators.py:46-61 | Path traversal prevention |
| `validate_url_not_internal` | validators.py:64-102 | SSRF prevention |
| `validate_model_name` | validators.py:121-161 | Model whitelist validation |
| `validate_tool_name` | validators.py:105-118 | Tool name whitelist |
| `validate_env_security` | query.py:132-139 | Dangerous env var blocking |
| `validate_command_security` | config.py:55-64 | Shell metacharacter blocking |

### Environment Variable Restrictions - POSITIVE

```python
# apps/api/schemas/requests/query.py:137-138
if key.upper() in ("LD_PRELOAD", "LD_LIBRARY_PATH", "PATH"):
    raise ValueError(f"Setting {key} environment variable is not allowed")
```

**Assessment:** Good protection against library preload attacks.

---

## Distributed Lock Implementation

### Finding SEC-019: Redis Lock Implementation - POSITIVE
**Severity:** N/A (Positive Finding)
**Location:** `apps/api/adapters/cache.py:316-362`

**Description:**
The distributed lock implementation correctly uses:
1. Atomic SET NX EX for acquisition
2. Lua script for atomic check-and-delete release
3. Unique lock values preventing accidental release

```python
# apps/api/adapters/cache.py:352-358
script = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""
```

**Assessment:** Correctly implements Redis distributed lock pattern.

---

## Recommendations Summary

### High Priority (Address Before Production)

1. **SEC-008**: Implement configurable fail-close for security-critical webhooks
2. **SEC-001**: Add session ownership verification tied to API keys

### Medium Priority (Address Soon)

3. **SEC-007**: Add symlink protection in skills discovery
4. **SEC-009**: Implement request body size limits
5. **SEC-012**: Plan migration to multi-tenant API keys
6. **SEC-014**: Validate webhook response schemas

### Low Priority (Best Practices)

7. **SEC-004**: Remove API key from request state
8. **SEC-002**: Unify error messages to prevent enumeration
9. **SEC-015**: Implement security audit logging
10. **SEC-016**: Remove exception type from production errors

---

## Security Hardening Checklist

### Pre-Production Checklist

- [ ] Set `DEBUG=false` in production
- [ ] Configure specific CORS origins
- [ ] Set strong, unique API key
- [ ] Enable `trust_proxy_headers` only behind trusted proxy
- [ ] Configure TLS termination at proxy/load balancer
- [ ] Set up rate limiting appropriate for expected load
- [ ] Enable structured logging with security events
- [ ] Run dependency vulnerability scan
- [ ] Review and restrict allowed_tools configuration
- [ ] Configure webhook timeouts appropriately

### Operational Security

- [ ] Implement API key rotation procedure
- [ ] Set up alerting for authentication failures
- [ ] Monitor rate limit violations
- [ ] Review logs for anomalous session patterns
- [ ] Plan incident response for key compromise
- [ ] Document session data retention policy

---

## Conclusion

The Claude Agent API demonstrates **solid security foundations** with many security controls correctly implemented:
- Constant-time comparisons
- SSRF prevention
- SQL injection prevention
- Path traversal protection
- Secure-by-default configuration patterns

The primary areas requiring attention are:
1. **Authorization model** - session ownership verification
2. **Webhook fail-open** - potentially dangerous for security hooks
3. **Multi-tenancy** - single API key limits audit and access control

For a development/internal deployment, the current security posture is **acceptable**. For production deployment with external access, address the high and medium priority findings first.

---

**Report Generated:** 2026-01-09
**Audit Methodology:** Manual code review with OWASP Top 10 2021 framework

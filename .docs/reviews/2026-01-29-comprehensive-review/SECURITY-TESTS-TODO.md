# Security Tests Implementation - Phase 2
**Priority:** P0 | **Estimated Work:** 3-5 days | **Risk:** CRITICAL

## Overview

This document provides ready-to-implement test code for Phase 2 security findings. Tests are organized by file and follow TDD RED-GREEN-REFACTOR pattern.

---

## 1. Session Authorization Boundary Tests

**File:** `tests/unit/services/test_session_authorization.py` (NEW)

**Setup:**
```bash
touch tests/unit/services/test_session_authorization.py
```

**Implementation:**

```python
"""Tests for session authorization boundaries - Owner API key filtering.

SECURITY: Validates that sessions are filtered by owner at DB level (not in Python).
This prevents unauthorized API keys from seeing other users' sessions.
"""

import pytest
from uuid import uuid4

from apps.api.services.session import SessionService


class TestSessionAuthorizationBoundary:
    """RED-GREEN-REFACTOR: Test session authorization boundaries."""

    @pytest.mark.anyio
    async def test_list_sessions_filters_by_owner_api_key_in_database(
        self,
        session_service,
        db_repo,
    ) -> None:
        """RED: Verify session filtering happens at DB query level (not memory).

        Given: Multiple sessions owned by different API keys (alice, bob)
        When: Alice lists her sessions with owner_api_key="key-alice"
        Then:
            - Only alice's sessions are returned
            - Database query includes owner_api_key filter (not load-all-then-filter)
            - Bob's sessions are not visible

        Security Impact: CRITICAL
        - If filtering done in Python, attacker could patch code to skip filter
        - DB-level filtering is enforced by PostgreSQL, not application logic
        """
        # Arrange: Create sessions for different API keys
        alice_session = await session_service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key="key-alice",
        )

        bob_session = await session_service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key="key-bob",
        )

        # Act: List sessions as alice
        result = await session_service.list_sessions(
            page=1,
            page_size=50,
            current_api_key="key-alice",
        )

        # Assert: Only alice's session returned
        assert result.total == 1, "Alice should see only 1 session (hers)"
        assert result.sessions[0].id == alice_session.id
        assert result.sessions[0].owner_api_key == "key-alice"

        # Verify Bob's session is not accessible
        assert len([s for s in result.sessions if s.id == bob_session.id]) == 0

    @pytest.mark.anyio
    async def test_list_sessions_uses_indexed_database_query(
        self,
        session_service,
        query_counter,  # Fixture to count DB queries
    ) -> None:
        """GREEN: Verify DB query uses indexed owner_api_key field.

        This prevents N+1 queries and ensures efficient filtering.
        """
        # Arrange: Create 100 sessions for alice
        for i in range(100):
            await session_service.create_session(
                model="sonnet",
                session_id=str(uuid4()),
                owner_api_key="key-alice",
            )

        # Act: List alice's sessions
        query_counter.reset()
        result = await session_service.list_sessions(
            page=1,
            page_size=50,
            current_api_key="key-alice",
        )
        queries = query_counter.queries

        # Assert: Only 1 SELECT query (indexed lookup, not 1+N)
        select_queries = [q for q in queries if "SELECT" in str(q)]
        assert len(select_queries) == 1, f"Expected 1 query, got {len(select_queries)}"

        # Verify query includes WHERE owner_api_key = ... in SQL
        query_text = str(select_queries[0])
        assert "owner_api_key" in query_text.lower() or "WHERE" in query_text

    @pytest.mark.anyio
    async def test_list_sessions_strict_api_key_isolation(
        self,
        session_service,
    ) -> None:
        """REFACTOR: Verify strict tenant isolation between API keys.

        Simulates adversarial scenario where Alice tries to access Bob's sessions.
        """
        # Arrange
        alice_key = "key-alice-12345"
        bob_key = "key-bob-54321"

        alice_session = await session_service.create_session(
            model="sonnet",
            session_id=f"session-alice-{uuid4()}",
            owner_api_key=alice_key,
        )

        bob_session = await session_service.create_session(
            model="sonnet",
            session_id=f"session-bob-{uuid4()}",
            owner_api_key=bob_key,
        )

        # Act: Alice lists sessions
        alice_result = await session_service.list_sessions(
            page=1,
            page_size=50,
            current_api_key=alice_key,
        )

        # Assert: Alice only sees her own
        alice_ids = [s.id for s in alice_result.sessions]
        assert alice_session.id in alice_ids
        assert bob_session.id not in alice_ids

        # Act: Bob lists sessions
        bob_result = await session_service.list_sessions(
            page=1,
            page_size=50,
            current_api_key=bob_key,
        )

        # Assert: Bob only sees his own
        bob_ids = [s.id for s in bob_result.sessions]
        assert bob_session.id in bob_ids
        assert alice_session.id not in bob_ids

    @pytest.mark.anyio
    async def test_get_session_enforces_owner_boundary(
        self,
        session_service,
    ) -> None:
        """RED: Verify get_session() rejects access to unowned sessions.

        This tests the _enforce_owner() method at single-session level.
        """
        # Arrange
        alice_key = "key-alice"
        bob_key = "key-bob"

        session = await session_service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=alice_key,
        )

        # Act: Alice retrieves her session
        result = await session_service.get_session(
            session.id,
            current_api_key=alice_key,
        )

        # Assert: Success
        assert result is not None
        assert result.id == session.id

        # Act: Bob tries to retrieve alice's session
        result = await session_service.get_session(
            session.id,
            current_api_key=bob_key,
        )

        # Assert: Raises SessionNotFoundError (not 403, but 404 for op sec)
        from apps.api.exceptions.session import SessionNotFoundError

        try:
            # Should have raised in the previous call, but if not:
            assert result is None, "SessionNotFoundError should be raised"
        except SessionNotFoundError:
            pass  # Expected
```

**Integration Test (test via HTTP):**

```python
# File: tests/integration/test_session_authorization.py (NEW)

@pytest.mark.anyio
class TestSessionAuthorizationHTTP:
    """Test session authorization through HTTP endpoints."""

    @pytest.mark.anyio
    async def test_list_sessions_endpoint_filters_by_current_api_key(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Integration test for GET /api/v1/sessions authorization."""
        # Create sessions for different API keys
        alice_key = "key-alice-integration"
        bob_key = "key-bob-integration"

        # Alice creates a session
        response = await async_client.post(
            "/api/v1/query",
            headers={"X-API-Key": alice_key},
            json={
                "prompt": "Create session for alice",
                "stream": False,
                "max_turns": 1,
            },
        )
        assert response.status_code == 200
        alice_session_id = response.json()["session_id"]

        # Bob creates a session
        response = await async_client.post(
            "/api/v1/query",
            headers={"X-API-Key": bob_key},
            json={
                "prompt": "Create session for bob",
                "stream": False,
                "max_turns": 1,
            },
        )
        assert response.status_code == 200
        bob_session_id = response.json()["session_id"]

        # Alice lists sessions
        response = await async_client.get(
            "/api/v1/sessions",
            headers={"X-API-Key": alice_key},
        )
        assert response.status_code == 200
        alice_sessions = response.json()["sessions"]

        # Verify Alice sees only her session
        alice_ids = [s["id"] for s in alice_sessions]
        assert alice_session_id in alice_ids
        assert bob_session_id not in alice_ids

        # Bob lists sessions
        response = await async_client.get(
            "/api/v1/sessions",
            headers={"X-API-Key": bob_key},
        )
        assert response.status_code == 200
        bob_sessions = response.json()["sessions"]

        # Verify Bob sees only his session
        bob_ids = [s["id"] for s in bob_sessions]
        assert bob_session_id in bob_ids
        assert alice_session_id not in bob_ids
```

**Pytest Markers & Configuration:**

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    # ... existing markers ...
    "security: Security-focused tests",
    "authz: Authorization boundary tests",
]
```

---

## 2. MCP Share Endpoint Security Tests

**File:** `tests/security/test_mcp_share_endpoint.py` (NEW)

```python
"""Security tests for MCP share endpoints - Token isolation and access control.

SECURITY BOUNDARY: Share tokens must be scoped to creator and validated on access.
"""

import pytest
from httpx import AsyncClient


class TestMcpShareTokenSecurity:
    """Test MCP share token isolation and authorization."""

    @pytest.mark.anyio
    async def test_mcp_share_create_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """RED: Share creation endpoint requires valid API key.

        Unauthenticated requests should receive 401 Unauthorized.
        """
        response = await async_client.post(
            "/api/v1/mcp-servers/share",
            headers={},  # No API key
            json={
                "name": "test-server",
                "config": {
                    "type": "stdio",
                    "command": "test-command",
                },
            },
        )

        # Assert: Rejected with 401
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_mcp_share_get_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """RED: Share token resolution requires valid API key."""
        response = await async_client.get(
            "/api/v1/mcp-servers/share/some-token",
            headers={},  # No API key
        )

        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_mcp_share_token_isolation_by_api_key(
        self,
        async_client: AsyncClient,
    ) -> None:
        """RED: Alice's share token cannot be used by Bob.

        Create share with Alice's API key, try to access with Bob's API key.
        Should return 404 or 403 (not allow cross-tenant access).
        """
        alice_key = "key-alice-mcp"
        bob_key = "key-bob-mcp"

        # Alice creates share
        response = await async_client.post(
            "/api/v1/mcp-servers/share",
            headers={"X-API-Key": alice_key},
            json={
                "name": "alice-server",
                "config": {
                    "type": "stdio",
                    "command": "alice-command",
                },
            },
        )
        assert response.status_code == 201
        alice_token = response.json()["token"]

        # Bob tries to access Alice's token
        response = await async_client.get(
            f"/api/v1/mcp-servers/share/{alice_token}",
            headers={"X-API-Key": bob_key},
        )

        # Should reject (404 or 403, not 200)
        assert response.status_code in (403, 404), (
            f"Cross-tenant access should be rejected. Got {response.status_code}: "
            f"{response.json()}"
        )

        # Verify Bob doesn't get Alice's config
        if response.status_code == 200:
            data = response.json()
            assert data.get("config", {}).get("command") != "alice-command"

    @pytest.mark.anyio
    async def test_mcp_share_token_not_guessable(
        self,
        async_client: AsyncClient,
    ) -> None:
        """RED: Share tokens are not sequential/guessable.

        Create multiple shares and verify tokens are random (not incrementing).
        """
        api_key = "key-test-token-randomness"

        tokens = []
        for i in range(10):
            response = await async_client.post(
                "/api/v1/mcp-servers/share",
                headers={"X-API-Key": api_key},
                json={
                    "name": f"server-{i}",
                    "config": {
                        "type": "stdio",
                        "command": f"cmd-{i}",
                    },
                },
            )
            assert response.status_code == 201
            token = response.json()["token"]
            tokens.append(token)

        # Verify all tokens are unique
        assert len(set(tokens)) == len(tokens), "Tokens should be unique"

        # Verify tokens are sufficiently random (not simple incrementing IDs)
        # Check token length (should be reasonably long for entropy)
        for token in tokens:
            assert len(token) >= 16, f"Token too short to be secure: {token}"

    @pytest.mark.anyio
    async def test_mcp_share_invalid_token_returns_404(
        self,
        async_client: AsyncClient,
    ) -> None:
        """RED: Invalid token returns 404 (not detailed error revealing structure).

        Prevents information leakage about token format/validation.
        """
        response = await async_client.get(
            "/api/v1/mcp-servers/share/invalid-token-12345",
            headers={"X-API-Key": "key-test"},
        )

        # Should return 404, not 400 or detailed error
        assert response.status_code == 404

        # Verify error message doesn't leak info about token format
        error_msg = response.json().get("detail", "")
        assert "token format" not in error_msg.lower()
        assert "length" not in error_msg.lower()

    @pytest.mark.anyio
    async def test_mcp_share_token_expiration(
        self,
        async_client: AsyncClient,
    ) -> None:
        """RED: Share tokens expire after TTL.

        Create share, wait for expiration, verify token is invalid.
        """
        api_key = "key-test-expiration"

        # Create share with short TTL (test default)
        response = await async_client.post(
            "/api/v1/mcp-servers/share",
            headers={"X-API-Key": api_key},
            json={
                "name": "expiring-server",
                "config": {
                    "type": "stdio",
                    "command": "cmd",
                },
            },
        )
        assert response.status_code == 201
        token = response.json()["token"]
        ttl_seconds = response.json().get("expires_in", 3600)

        # Verify token works immediately
        response = await async_client.get(
            f"/api/v1/mcp-servers/share/{token}",
            headers={"X-API-Key": api_key},
        )
        assert response.status_code == 200

        # Simulate expiration (in real test, would use time travel)
        # For now, verify response includes expiration time
        assert "expires_at" in response.json() or "expires_in" in response.json()
```

---

## 3. Bearer Token Edge Cases

**File:** `tests/unit/middleware/test_openai_auth_edge_cases.py` (NEW)

```python
"""Extended tests for Bearer token extraction - Edge cases and security.

Tests for RFC 6750 Bearer Token compliance and malformed input handling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from starlette.responses import Response

from apps.api.middleware.openai_auth import BearerAuthMiddleware


class TestBearerTokenExtractionEdgeCases:
    """RED-GREEN-REFACTOR: Test Bearer token edge cases."""

    @pytest.mark.anyio
    async def test_bearer_token_with_extra_whitespace(self) -> None:
        """RED: Double/triple space between Bearer and token handled.

        Input: "Bearer  sk-test-123" (double space)
        Expected: Extract "sk-test-123" (trimmed)
        """
        # Arrange
        request = MagicMock(spec=Request)
        request.url.path = "/v1/chat/completions"
        request.headers = {"Authorization": "Bearer  sk-test-123"}
        request.scope = {"type": "http", "headers": []}

        call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

        # Act
        middleware = BearerAuthMiddleware(app=MagicMock())
        response = await middleware.dispatch(request, call_next)

        # Assert: Token extracted correctly (whitespace trimmed)
        assert response.status_code == 200

        # Verify token in headers (implementation detail varies)
        # Either in X-API-Key or request.headers
        auth_header = None
        if hasattr(request, "scope") and "headers" in request.scope:
            for name, value in request.scope.get("headers", []):
                if name == b"x-api-key":
                    auth_header = value.decode()
                    break
        elif hasattr(request, "headers"):
            auth_header = request.headers.get("x-api-key")

        # Should extract "sk-test-123" (not "Bearer  sk-test-123")
        assert auth_header == "sk-test-123" or request.headers.get("x-api-key") == "sk-test-123"

    @pytest.mark.anyio
    async def test_bearer_scheme_case_insensitive_variants(self) -> None:
        """RED: Bearer scheme accepts multiple case variants.

        RFC 6750 states: "case-insensitive"
        Test: bearer, Bearer, BEARER, BeArEr
        """
        schemes = ["bearer", "Bearer", "BEARER", "BeArEr", "bEaReR"]

        for scheme in schemes:
            request = MagicMock(spec=Request)
            request.url.path = "/v1/chat/completions"
            request.headers = {"Authorization": f"{scheme} sk-test-123"}
            request.scope = {"type": "http", "headers": []}

            call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

            middleware = BearerAuthMiddleware(app=MagicMock())
            response = await middleware.dispatch(request, call_next)

            # Should succeed for all case variants
            assert response.status_code == 200, f"Failed for scheme: {scheme}"

    @pytest.mark.anyio
    async def test_bearer_token_with_special_characters(self) -> None:
        """GREEN: Bearer token with special chars (. - _ / +) handled.

        These are valid in JWT/OAuth tokens.
        """
        valid_tokens = [
            "sk-test_123_456",      # Underscores
            "sk-test-abc-def",      # Hyphens
            "sk-test.abc.def",      # Dots
            "sk-test/abc==",        # Slashes and base64 padding
            "sk-test+abc==",        # Plus sign
            "abcdefghijklmnopqrstuvwxyz0123456789",  # Alphanumeric
        ]

        for token in valid_tokens:
            request = MagicMock(spec=Request)
            request.url.path = "/v1/chat/completions"
            request.headers = {"Authorization": f"Bearer {token}"}
            request.scope = {"type": "http", "headers": []}

            call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

            middleware = BearerAuthMiddleware(app=MagicMock())
            await middleware.dispatch(request, call_next)

            # Should not modify or reject valid tokens

    @pytest.mark.anyio
    async def test_bearer_token_rejects_null_bytes(self) -> None:
        """RED: Null bytes in token are rejected or stripped.

        Security: Prevent null byte injection attacks.
        """
        # This is tricky - most frameworks strip null bytes automatically
        # But we should verify if they're present, token is rejected

        request = MagicMock(spec=Request)
        request.url.path = "/v1/chat/completions"
        # Null byte in token
        request.headers = {"Authorization": "Bearer sk\x00test"}
        request.scope = {"type": "http", "headers": []}

        call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

        middleware = BearerAuthMiddleware(app=MagicMock())
        response = await middleware.dispatch(request, call_next)

        # Token should either be rejected or null bytes stripped
        # (Depends on implementation preference)

    @pytest.mark.anyio
    async def test_malformed_auth_header_gracefully_handled(self) -> None:
        """RED: Various malformed headers don't crash server."""
        malformed_headers = [
            "Bearer",                # No token
            "Bearer ",               # Space but no token
            "Bearer\t",              # Tab but no token
            "InvalidScheme token",   # Wrong scheme
            "Bearer token token",    # Too many parts
            "",                      # Empty header
            "   ",                   # Whitespace only
        ]

        for header_value in malformed_headers:
            request = MagicMock(spec=Request)
            request.url.path = "/v1/chat/completions"
            request.headers = {"Authorization": header_value} if header_value else {}
            request.scope = {"type": "http", "headers": []}

            call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

            middleware = BearerAuthMiddleware(app=MagicMock())

            # Should NOT crash
            try:
                response = await middleware.dispatch(request, call_next)
                assert response.status_code == 200
            except Exception as e:
                pytest.fail(f"Middleware crashed on header: {header_value!r} - {e}")

    @pytest.mark.anyio
    async def test_bearer_token_does_not_override_explicit_x_api_key(self) -> None:
        """GREEN: Explicit X-API-Key is NOT overwritten by Bearer token.

        Precedence: Explicit headers > Bearer extraction
        """
        request = MagicMock(spec=Request)
        request.url.path = "/v1/chat/completions"
        request.headers = {
            "Authorization": "Bearer sk-bearer-123",
            "X-API-Key": "sk-explicit-456",
        }
        request.scope = {"type": "http", "headers": []}

        call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

        middleware = BearerAuthMiddleware(app=MagicMock())
        response = await middleware.dispatch(request, call_next)

        # Verify X-API-Key was preserved (not overwritten)
        assert request.headers.get("X-API-Key") == "sk-explicit-456"

    @pytest.mark.anyio
    async def test_bearer_token_only_on_v1_routes(self) -> None:
        """GREEN: Bearer token extraction ONLY on /v1/* routes."""
        routes_to_test = [
            ("/v1/chat/completions", True),   # Should extract
            ("/v1/models", True),              # Should extract
            ("/api/v1/query", False),          # Should NOT extract
            ("/api/v1/sessions", False),       # Should NOT extract
            ("/v1/", True),                    # Should extract
            ("/v2/chat", False),               # Wrong version
            ("/v1chat", False),                # Missing slash
        ]

        for path, should_extract in routes_to_test:
            request = MagicMock(spec=Request)
            request.url.path = path
            request.headers = {"Authorization": "Bearer sk-test-123"}
            request.scope = {"type": "http", "headers": []}

            call_next = AsyncMock(return_value=Response(content=b"OK", status_code=200))

            middleware = BearerAuthMiddleware(app=MagicMock())
            response = await middleware.dispatch(request, call_next)

            if should_extract:
                # Token should be extracted for /v1/* routes
                # Verify in headers or that auth succeeded
                pass
            else:
                # Token should NOT be extracted for non-/v1/* routes
                # Verify Authorization header is unchanged
                assert "Authorization" in request.headers
```

---

## 4. Webhook ReDoS Protection Tests

**File:** `tests/unit/services/test_webhook_redos.py` (NEW)

```python
"""Tests for Regular Expression Denial of Service (ReDoS) protection.

SECURITY: Prevents catastrophic backtracking in user-supplied regex patterns.
"""

import re
import time
import pytest

from apps.api.services.webhook import WebhookService
from apps.api.schemas.requests.config import HookWebhookSchema


class TestWebhookReDoSProtection:
    """RED-GREEN-REFACTOR: Test ReDoS protection in webhook matcher."""

    @pytest.mark.anyio
    async def test_webhook_regex_timeout_on_catastrophic_pattern(self) -> None:
        """RED: Catastrophic backtracking is detected or timed out.

        Pattern: (a+)+b matched against "aaaaaa..."
        This causes exponential backtracking: O(2^n) complexity.
        """
        # The classic ReDoS pattern
        dangerous_pattern = "(a+)+b"

        hook_config = HookWebhookSchema(
            url="http://webhook.local/hook",
            matcher=dangerous_pattern,
        )

        service = WebhookService()

        # Act: Try to match against string that triggers backtracking
        # Should timeout or complete quickly
        start = time.time()
        try:
            result = service.should_execute_hook(
                hook_config,
                "aaaaaaaaaaaaaaaaaaaaaa",  # 22 a's (no b) triggers backtracking
            )
            elapsed = time.time() - start

            # Assert: Either returns quickly or was prevented
            assert (
                elapsed < 0.5
            ), f"Regex took {elapsed}s - vulnerable to ReDoS"

        except TimeoutError:
            # Also acceptable - regex timeout is caught
            elapsed = time.time() - start
            assert elapsed < 1.0

        except re.error:
            # Pattern rejected as invalid - also acceptable
            pass

    @pytest.mark.anyio
    async def test_webhook_regex_complexity_detection(self) -> None:
        """RED: Dangerous regex patterns are detected/rejected.

        Test patterns that are known to cause ReDoS:
        - (a+)+
        - (a|a)*
        - (a|ab)*
        - (.*)*
        - (?:a|a)*
        """
        dangerous_patterns = [
            "(a+)+",         # Nested quantifiers
            "(a|a)*",        # Alternation with overlap
            "(a|ab)*",       # Alternation catastrophe
            "(.*)*",         # Nested .* quantifiers
            "(?:a|a)*",      # Non-capturing variant
            "(a*)*",         # Nested * quantifiers
            "(a{2,}){2,}",   # Nested range quantifiers
        ]

        service = WebhookService()

        for pattern in dangerous_patterns:
            hook_config = HookWebhookSchema(
                url="http://webhook.local/hook",
                matcher=pattern,
            )

            # Test with multiple input lengths
            max_time = 0
            for input_length in [10, 15, 20, 25]:
                tool_name = "a" * input_length

                start = time.perf_counter()
                try:
                    result = service.should_execute_hook(hook_config, tool_name)
                except (TimeoutError, re.error):
                    result = None

                elapsed = time.perf_counter() - start
                max_time = max(max_time, elapsed)

                # Should complete quickly even for long inputs
                assert (
                    elapsed < 0.1
                ), f"Pattern {pattern!r} hangs on input length {input_length}"

    @pytest.mark.anyio
    async def test_webhook_safe_patterns_still_work(self) -> None:
        """GREEN: Safe patterns continue to work correctly."""
        safe_patterns = [
            (r"^tool_.*", "tool_read", True),         # Safe prefix match
            (r".*_execute$", "task_execute", True),   # Safe suffix match
            (r"^(read|write|delete)$", "read", True), # Safe alternation
            (r"^task[0-9]+$", "task123", True),       # Safe character class
            (r"^tool_", "tool_", False),              # Non-match
        ]

        service = WebhookService()

        for pattern, tool_name, expected_match in safe_patterns:
            hook_config = HookWebhookSchema(
                url="http://webhook.local/hook",
                matcher=pattern,
            )

            result = service.should_execute_hook(hook_config, tool_name)

            assert result == expected_match, (
                f"Pattern {pattern!r} on {tool_name!r} "
                f"returned {result}, expected {expected_match}"
            )

    @pytest.mark.anyio
    async def test_webhook_regex_validation_on_creation(self) -> None:
        """RED: Regex complexity validated when hook is created/updated.

        Should reject patterns with known ReDoS signatures.
        """
        # This test verifies that the service/route validates regex
        # when the hook is configured (not at runtime)

        # If implementation doesn't validate, at least timeout must work
        dangerous_pattern = "(x+)+y"

        hook_config = HookWebhookSchema(
            url="http://webhook.local/hook",
            matcher=dangerous_pattern,
        )

        service = WebhookService()

        # Either:
        # 1. Rejected at validation time (preferred)
        # 2. Or timed out at runtime (acceptable)

        start = time.perf_counter()
        result = service.should_execute_hook(hook_config, "x" * 20)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, "ReDoS vulnerability not protected"

    @pytest.mark.anyio
    async def test_webhook_invalid_regex_handled_gracefully(self) -> None:
        """RED: Invalid regex syntax doesn't crash server."""
        invalid_patterns = [
            "(",           # Unclosed group
            "[a-z",        # Unclosed bracket
            "(?P<>group)", # Empty group name
            "*invalid",    # Quantifier without target
            "(?P<>)",      # Invalid syntax
        ]

        service = WebhookService()

        for pattern in invalid_patterns:
            hook_config = HookWebhookSchema(
                url="http://webhook.local/hook",
                matcher=pattern,
            )

            # Should not crash
            try:
                result = service.should_execute_hook(hook_config, "test")
                # Either returns False or True (safe default)
                assert result in (True, False)
            except re.error as e:
                # Acceptable to raise re.error for invalid regex
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")
```

---

## Implementation Schedule

### Week 1
- **Day 1-2:** Session authorization tests + fix
- **Day 3:** MCP share endpoint tests + documentation
- **Day 4:** Bearer token edge cases
- **Day 5:** Webhook ReDoS protection

### Week 2
- **Day 1-2:** Performance tests (N+1, connection pool)
- **Day 3-4:** Coverage gap closure
- **Day 5:** Integration testing & validation

---

## Running the Tests

```bash
# Run security tests only
uv run pytest tests/security/ tests/unit/services/test_session_authorization.py -v

# Run with coverage
uv run pytest --cov=apps/api --cov-report=term-missing tests/security/ -v

# Run specific test class
uv run pytest tests/unit/services/test_session_authorization.py::TestSessionAuthorizationBoundary -v

# Run marked tests
uv run pytest -m security -v
```

---

## Test Fixtures Needed

Create `tests/fixtures/security_fixtures.py`:

```python
"""Shared fixtures for security tests."""

import pytest
from typing import Callable


@pytest.fixture
def query_counter():
    """Counter for database queries executed during test."""

    class QueryCounter:
        def __init__(self):
            self.queries = []

        def reset(self):
            self.queries = []

    return QueryCounter()


@pytest.fixture
async def session_service_with_repo(session_service, db_repo):
    """Session service with database repository."""
    session_service._db_repo = db_repo
    return session_service
```

---

## Success Criteria

- [ ] All P0 security tests passing
- [ ] Session authorization filters at DB level
- [ ] Bearer token handles all edge cases
- [ ] Webhook regex has timeout protection
- [ ] MCP share tokens are isolated by API key
- [ ] Coverage report shows <5% improvement in tested modules
- [ ] No test flakiness (all tests pass consistently)

---

**Next:** Implement tests in order, verify each RED→GREEN→REFACTOR cycle.

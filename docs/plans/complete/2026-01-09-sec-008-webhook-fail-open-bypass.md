# SEC-008 Webhook Fail-Open Security Bypass Implementation Plan

> **Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure PreToolUse hooks fail closed by denying tool execution when webhook callbacks error or time out.

**Architecture:** Centralize webhook error handling in `WebhookService` with an event-aware default decision helper that returns `deny` for `PreToolUse` and `allow` for non-blocking hooks, then update error paths to use it. Update unit tests to assert fail-closed behavior for `PreToolUse` errors.

**Tech Stack:** Python 3.11, httpx, structlog, pytest.

---

### Task 1: Lock in fail-closed behavior for PreToolUse errors (tests first)

**Files:**
- Modify: `tests/unit/test_webhook_service.py`

**Step 1: Update existing tests to expect fail-closed behavior**

Modify the three existing error-handling tests in the `TestWebhookErrorHandling` class (lines 324-394 in `tests/unit/test_webhook_service.py`) to expect `deny` instead of `allow` for `PreToolUse` errors:

1. `test_connection_error_returns_default` (line 328):
   - Change line 348 assertion from `assert result["decision"] == "allow"` to `assert result["decision"] == "deny"`
   - Update line 349 to verify error is mentioned: `assert "error" in result.get("reason", "").lower()`

2. `test_invalid_json_response_returns_default` (line 352):
   - Change line 371 assertion from `assert result["decision"] == "allow"` to `assert result["decision"] == "deny"`

3. `test_http_error_status_returns_default` (line 374):
   - Change line 393 assertion from `assert result["decision"] == "allow"` to `assert result["decision"] == "deny"`

Expected changes:
```python
# In test_connection_error_returns_default (line 328-350):
        # Change from:
        assert result["decision"] == "allow"
        assert "error" in result.get("reason", "").lower()

        # To:
        assert result["decision"] == "deny"
        assert "error" in result.get("reason", "").lower()

# In test_invalid_json_response_returns_default (line 352-372):
        # Change from:
        assert result["decision"] == "allow"

        # To:
        assert result["decision"] == "deny"

# In test_http_error_status_returns_default (line 374-394):
        # Change from:
        assert result["decision"] == "allow"

        # To:
        assert result["decision"] == "deny"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_webhook_service.py::TestWebhookErrorHandling -v`

Expected: FAIL (currently returns `allow` on errors).

**Step 3: Implement minimal fail-closed logic**

Update `apps/api/services/webhook.py`:

**Part A: Add _error_response helper method**

Add this method after line 89 (after `__init__` method, before `execute_hook`):

```python
    def _error_response(self, hook_event: HookEventType, reason: str) -> dict[str, object]:
        """Return appropriate error response based on hook event type.

        PreToolUse hooks fail closed (deny), all others fail open (allow).

        Args:
            hook_event: Type of hook event that encountered an error.
            reason: Description of the error that occurred.

        Returns:
            Dictionary with 'decision' and 'reason' fields.
        """
        decision: DecisionType = "deny" if hook_event == "PreToolUse" else "allow"
        return {
            "decision": decision,
            "reason": reason,
        }
```

**Part B: Update all four error handlers in execute_hook()**

Replace the return statements in each error handler:

1. **TimeoutError handler** (lines 138-148): Replace lines 145-148 with:
```python
            return self._error_response(
                hook_event,
                f"Webhook timeout after {hook_config.timeout}s",
            )
```

2. **ConnectionError handler** (lines 149-159): Replace lines 156-159 with:
```python
            return self._error_response(
                hook_event,
                f"Webhook connection error: {e!s}",
            )
```

3. **WebhookHttpError handler** (lines 160-171): Replace lines 168-171 with:
```python
            return self._error_response(
                hook_event,
                f"Webhook HTTP error: {e.message}",
            )
```

4. **ValueError handler** (lines 172-182): Replace lines 179-182 with:
```python
            return self._error_response(
                hook_event,
                f"Invalid JSON response: {e!s}",
            )
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_webhook_service.py::TestWebhookErrorHandling -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/unit/test_webhook_service.py apps/api/services/webhook.py
git commit -m "fix(security): fail closed on PreToolUse webhook errors"
```

### Task 2: Update security audit docs for the fix

**Files:**
- Modify: `.docs/audit-summary.md`
- Modify: `.docs/quick-wins-checklist.md`

**Action:**

Update both files to mark SEC-008 as fixed. Add this snippet under the SEC-008 entry in each file:

```markdown
**Status**: Fixed
**Note**: PreToolUse webhooks now fail closed; connection/timeout/HTTP/JSON errors return `deny`.
```

**Verification:**

After updating, verify the change is present:

```bash
rg -n "PreToolUse webhooks now fail closed" .docs/audit-summary.md .docs/quick-wins-checklist.md
```

Expected: Should find the new note in both files.

**Commit:**

```bash
git add .docs/audit-summary.md .docs/quick-wins-checklist.md
git commit -m "docs: mark SEC-008 fail-closed webhook fix"
```

---

**Notes:** Follow @test-driven-development and @verification-before-completion for each task.

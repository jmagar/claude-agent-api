# AgentServiceConfig Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **📁 Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

**Goal:** Remove backward-compatible `AgentService` constructor params and enforce `AgentServiceConfig` across all instantiations.

**Architecture:** `AgentService` must be constructed with a single `AgentServiceConfig` plus explicit core collaborators (session tracker, runners, etc.). All call sites should build `AgentServiceConfig` and pass it to `AgentService`. Stream and single-query runners must receive canonical kwargs unconditionally. Test stubs must match canonical runner signatures.

**Tech Stack:** Python 3.12, FastAPI, pytest, ruff, ty.

---

### Task 0: Inventory All AgentService Instantiations

**Files:**
- Scan: repo-wide

**Step 1: Find all constructor calls**

Run:
- `rg -n "AgentService\(" apps tests`

Expected: list of all direct instantiations to update. Capture file list for Tasks 2–5.

**Step 2: Create a checklist of files to update**

At minimum (from current repo scan):
- `apps/api/services/agent/service.py`
- `apps/api/dependencies.py`
- `apps/api/routes/agents.py`
- `tests/conftest.py`
- `tests/unit/test_agent_service.py`
- `tests/unit/test_dependencies.py`
- `tests/integration/test_distributed_sessions.py`
- `tests/integration/test_websocket.py`
- `tests/integration/test_sdk_errors.py`

---

### Task 1: Enforce Config-Only AgentService Constructor

**Files:**
- Modify: `apps/api/services/agent/service.py`
- Test: `tests/unit/test_agent_service.py`

**Step 1: Write/adjust failing tests (constructor callers)**

Update tests that currently pass legacy params to use `AgentServiceConfig`:

```python
from apps.api.services.agent.config import AgentServiceConfig

config = AgentServiceConfig(cache=mock_cache)
service = AgentService(config=config)
```

Checkpoint usage:

```python
config = AgentServiceConfig(checkpoint_service=mock_checkpoint_service)
service = AgentService(config=config)
```

**Step 2: Run test to verify failure before implementation**

Run:
- `uv run pytest tests/unit/test_agent_service.py::TestEnableFileCheckpointing::test_agent_service_accepts_checkpoint_service_dependency -v`

Expected: FAIL until production constructor is updated.

**Step 3: Implement minimal constructor change**

In `apps/api/services/agent/service.py`:
- Remove params: `cache`, `checkpoint_service`, `memory_service`, `mcp_config_injector`, `webhook_service`.
- Keep `config: AgentServiceConfig | None` and explicit collaborators (session_tracker, runners, etc.).
- When `config is None`, create `AgentServiceConfig()` with defaults only.
- Remove all compatibility logic that merges legacy args into config.

**Step 4: Run test to verify pass**

Run:
- `uv run pytest tests/unit/test_agent_service.py::TestEnableFileCheckpointing::test_agent_service_accepts_checkpoint_service_dependency -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/api/services/agent/service.py tests/unit/test_agent_service.py
git commit -m "refactor: require AgentServiceConfig in constructor"
```

---

### Task 2: Enforce Canonical Runner Signatures (Remove Conditional Kwargs)

**Files:**
- Modify: `apps/api/services/agent/service.py`
- Modify: `tests/unit/test_agent_service.py`

**Step 1: Update test stubs (fail first)**

Ensure stub runners accept canonical signature:

```python
async def run(self, request, commands_service, session_id_override=None, memory_service=None, api_key=""):
    ...
```

Run:
- `uv run pytest tests/unit/test_agent_service.py::TestQueryStreamSessionIds::test_query_stream_does_not_set_resume_session_id -v`

Expected: FAIL until production stops using conditional kwargs or stubs updated.

**Step 2: Implement canonical kwargs in production**

In `apps/api/services/agent/service.py`:
- Remove `_supports_param` helper.
- Call stream runner with canonical kwargs:
  - `session_id_override=session_id`
  - `memory_service=self._memory_service`
  - `api_key=api_key`
- Call single runner with canonical kwargs:
  - `memory_service=self._memory_service`
  - `api_key=api_key`

**Step 3: Run test to verify pass**

Run:
- `uv run pytest tests/unit/test_agent_service.py::TestQueryStreamSessionIds::test_query_stream_does_not_set_resume_session_id -v`

Expected: PASS.

**Step 4: Commit**

```bash
git add apps/api/services/agent/service.py tests/unit/test_agent_service.py
git commit -m "refactor: enforce canonical runner kwargs"
```

---

### Task 3: Update DI Layer to Build AgentServiceConfig Only

**Files:**
- Modify: `apps/api/dependencies.py`
- Test: `tests/unit/test_dependencies.py`

**Step 1: Update failing tests**

Use explicit config creation in tests:

```python
mock_cache = Mock(spec=RedisCache)
mock_checkpoint_service = Mock(spec=CheckpointService)
service = await get_agent_service(cache=mock_cache, checkpoint_service=mock_checkpoint_service)
```

**Step 2: Run test to verify failure before implementation**

Run:
- `uv run pytest tests/unit/test_dependencies.py::TestServiceDependencies::test_get_agent_service_creates_instance -v`

Expected: FAIL until DI builds config-only.

**Step 3: Implement DI changes**

In `apps/api/dependencies.py`:
- Build `AgentServiceConfig(checkpoint_service=checkpoint_service, cache=cache, mcp_config_injector=..., memory_service=..., webhook_service=...)`.
- Construct `AgentService(config=config)` only.

**Step 4: Run test to verify pass**

Run:
- `uv run pytest tests/unit/test_dependencies.py::TestServiceDependencies::test_get_agent_service_creates_instance -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/api/dependencies.py tests/unit/test_dependencies.py
git commit -m "refactor: DI builds AgentServiceConfig"
```

---

### Task 4: Update Tests/Fixtures to Use AgentServiceConfig

**Files:**
- Modify:
  - `tests/conftest.py`
  - `tests/integration/test_distributed_sessions.py`
  - `tests/integration/test_websocket.py`
  - `tests/integration/test_sdk_errors.py`
  - `tests/unit/test_agent_service.py`

**Step 1: Update constructor usage (fail first)**

Replace all legacy instantiations:

```python
config = AgentServiceConfig(cache=cache)
agent_service = AgentService(config=config)
```

Checkpoint usage:

```python
config = AgentServiceConfig(checkpoint_service=mock_checkpoint_service)
service = AgentService(config=config)
```

**Step 2: Run focused tests to confirm failures before implementation**

Run:
- `uv run pytest tests/integration/test_distributed_sessions.py -v`

Expected: FAIL until all constructor call sites updated.

**Step 3: Run focused tests to confirm success after updates**

Run:
- `uv run pytest tests/integration/test_distributed_sessions.py -v`
- `uv run pytest tests/integration/test_websocket.py -v`
- `uv run pytest tests/integration/test_sdk_errors.py -v`

Expected: PASS.

**Step 4: Commit**

```bash
git add tests/conftest.py tests/integration/test_distributed_sessions.py tests/integration/test_websocket.py tests/integration/test_sdk_errors.py tests/unit/test_agent_service.py
git commit -m "refactor: use AgentServiceConfig across tests and fixtures"
```

---

### Task 5: Update Application Routes That Instantiate AgentService Directly

**Files:**
- Modify: `apps/api/routes/agents.py`

**Step 1: Update instantiations (fail first)**

Replace any `AgentService(cache)` usage:

```python
from apps.api.services.agent.config import AgentServiceConfig

service = AgentService(config=AgentServiceConfig(cache=cache))
```

**Step 2: Run test to verify failure before implementation**

Run:
- `uv run pytest tests/integration/test_agents.py -v`

Expected: FAIL until route uses config-only.

**Step 3: Run test to verify pass after update**

Run:
- `uv run pytest tests/integration/test_agents.py -v`

Expected: PASS.

**Step 4: Commit**

```bash
git add apps/api/routes/agents.py
git commit -m "refactor: use AgentServiceConfig in routes"
```

---

### Task 6: Full Verification + Quality Gates

**Step 1: Full tests**

Run:
- `uv run pytest`

Expected: PASS (skips allowed for e2e/SDK).

**Step 2: Lint, format, typecheck**

Run:
- `make fmt`
- `make lint`
- `make typecheck`

Expected: all green.

**Step 3: Commit (if any fixes)**

```bash
git add -A
git commit -m "chore: enforce AgentServiceConfig-only construction"
```

---

## Notes
- Remove conditional kwargs in `AgentService` after stubs accept canonical signatures.
- Ensure all instantiations use `AgentServiceConfig` to avoid accidental legacy usage.
- Keep constructor signature strict to prevent future drift.

---

Plan complete and saved to `docs/plans/2026-02-05-agentservice-config-migration.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?

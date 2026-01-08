# Refactor Protocols - Separate Concerns Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

**Goal:** Separate Protocol interfaces from type/data definitions in `apps/api/protocols.py`.

**Architecture:** Move data classes (`SessionData`, `MessageData`, `CheckpointData`, `AgentMessage`) from `protocols.py` to `types.py`. Protocols remain in `protocols.py` and import the types. This follows the single-responsibility principle.

**Tech Stack:** Python 3.11+, typing.Protocol, TypedDict/dataclass patterns

---

## Current State Analysis

**File:** `apps/api/protocols.py` (391 lines)

| Lines | Content |
|-------|---------|
| 1-147 | `SessionRepository` Protocol |
| 148-303 | `Cache` Protocol |
| 305-348 | `AgentClient` Protocol |
| 350-391 | Data classes (SessionData, MessageData, CheckpointData, AgentMessage) |

**Problem:** Protocols (behavioral contracts) are mixed with data structures (type definitions). This violates separation of concerns.

**Target State:**
- `protocols.py`: Only Protocol interfaces
- `types.py`: All type definitions including data classes

---

## Task 1: Add Data Classes to types.py

**Files:**
- Modify: `apps/api/types.py` (append at end)

**Step 1: Add the data class imports and definitions**

Add at the end of `apps/api/types.py`:

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class SessionData:
    """Session data structure returned from repository."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str
    model: str
    working_directory: str | None
    total_turns: int
    total_cost_usd: float | None
    parent_session_id: UUID | None
    metadata: dict[str, object] | None


@dataclass
class MessageData:
    """Message data structure returned from repository."""

    id: UUID
    session_id: UUID
    message_type: str
    content: dict[str, object]
    created_at: datetime


@dataclass
class CheckpointData:
    """Checkpoint data structure returned from repository."""

    id: UUID
    session_id: UUID
    user_message_uuid: str
    created_at: datetime
    files_modified: list[str]


@dataclass
class AgentMessage:
    """Agent message structure from SDK client."""

    type: str
    data: dict[str, object]
```

**Step 2: Verify types.py is valid**

Run: `uv run python -c "from apps.api.types import SessionData, MessageData, CheckpointData, AgentMessage; print('OK')"`

Expected: `OK`

**Step 3: Commit**

```bash
git add apps/api/types.py
git commit -m "feat(types): add data classes from protocols"
```

---

## Task 2: Update protocols.py to Import from types.py

**Files:**
- Modify: `apps/api/protocols.py`

**Step 1: Update imports in protocols.py**

Replace the `TYPE_CHECKING` import block at lines 6-8:

```python
if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from datetime import datetime
```

With:

```python
if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from apps.api.types import (
        AgentMessage,
        CheckpointData,
        MessageData,
        SessionData,
    )
```

**Step 2: Remove data class definitions from protocols.py**

Delete lines 350-391 (the class definitions):

```python
# Type aliases for protocol return types
class SessionData:
    ...

class MessageData:
    ...

class CheckpointData:
    ...

class AgentMessage:
    ...
```

**Step 3: Verify protocols.py is valid**

Run: `uv run python -c "from apps.api.protocols import SessionRepository, Cache, AgentClient; print('OK')"`

Expected: `OK`

**Step 4: Run type checker**

Run: `uv run mypy apps/api/protocols.py apps/api/types.py`

Expected: No errors (or only pre-existing unrelated errors)

**Step 5: Commit**

```bash
git add apps/api/protocols.py
git commit -m "refactor(protocols): import data classes from types module"
```

---

## Task 3: Update Re-exports (if needed)

**Files:**
- Check: `apps/api/__init__.py`

**Step 1: Check if protocols.py re-exports data classes**

Run: `grep -n "SessionData\|MessageData\|CheckpointData\|AgentMessage" apps/api/__init__.py`

If any matches, update the imports to come from `types.py` instead of `protocols.py`.

**Step 2: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`

Expected: All tests pass

**Step 3: Run linting**

Run: `uv run ruff check apps/api/protocols.py apps/api/types.py`

Expected: No errors

**Step 4: Commit (if changes made)**

```bash
git add apps/api/__init__.py
git commit -m "refactor: update re-exports for data classes"
```

---

## Task 4: Final Verification

**Step 1: Verify imports work from both locations**

Run:
```bash
uv run python -c "
from apps.api.types import SessionData, MessageData, CheckpointData, AgentMessage
from apps.api.protocols import SessionRepository, Cache, AgentClient
print('All imports OK')
"
```

Expected: `All imports OK`

**Step 2: Run full type check**

Run: `uv run mypy apps/api/`

Expected: Pass (or only pre-existing errors)

**Step 3: Run full test suite with coverage**

Run: `uv run pytest tests/ -v --cov=apps/api --cov-report=term-missing`

Expected: All tests pass, coverage unchanged

---

## Summary

| Before | After |
|--------|-------|
| `protocols.py`: 391 lines (mixed concerns) | `protocols.py`: ~305 lines (protocols only) |
| Data classes defined inline | Data classes in `types.py` |
| Tight coupling | Clean separation |

**Files Changed:**
- `apps/api/types.py` - Added 4 data classes
- `apps/api/protocols.py` - Removed data classes, added import

**Total Commits:** 2-3 atomic commits

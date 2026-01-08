# Session: Split Request Schemas Refactoring

**Date**: 2026-01-08
**Duration**: Extended session (continued from previous context)
**Branch**: `001-claude-agent-api`

## Session Overview

Executed a comprehensive refactoring plan to split a 653-line monolithic `apps/api/schemas/requests.py` into a modular package structure. The work followed strict TDD principles with parallel subagent reviews after each task. Final cleanup removed backward compatibility re-exports in favor of explicit direct imports.

## Timeline

| Phase | Activity |
|-------|----------|
| 1 | Plan validation with 3 parallel agents (static-analyzer, environment-verifier, architecture-reviewer) |
| 2 | Tasks 1-6: Created modular schema files with TDD |
| 3 | Tasks 7-8: Verified/updated application and test imports |
| 4 | Task 9: Deleted original monolithic file |
| 5 | Task 10: Final verification (tests, types, linting) |
| 6 | Post-plan: Removed backward compat re-exports, updated all imports to direct paths |

## Key Findings

### Original Problem
- Monolithic `requests.py` at 653 lines violated single-responsibility principle
- Mixed concerns: config schemas, query schemas, session schemas, control schemas, validators
- Difficult to navigate and maintain

### Solution Architecture
```
apps/api/schemas/
├── validators.py           # Security validation (T128 patterns)
└── requests/
    ├── __init__.py         # Docstring only (no re-exports)
    ├── config.py           # 8 config schemas
    ├── query.py            # QueryRequest (30 fields, 6 validators)
    ├── sessions.py         # ResumeRequest, ForkRequest, AnswerRequest
    └── control.py          # ControlRequest, RewindRequest
```

### Security Validators (validators.py)
- `SHELL_METACHAR_PATTERN`: Detects shell injection attempts
- `PATH_TRAVERSAL_PATTERN`: Blocks `../` path traversal
- `NULL_BYTE_PATTERN`: Prevents null byte injection
- `BLOCKED_URL_PATTERNS`: SSRF protection for internal URLs

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| No re-exports in `__init__.py` | Pre-production codebase allows breaking changes; explicit imports are clearer |
| Security validators in separate module | Reusable across multiple schema files, single source of truth |
| TDD for each task | Ensures correctness, catches regressions early |
| Parallel subagent reviews | Spec compliance + code quality verification after each task |

## Files Modified

### Created (Task 1-6)
| File | Purpose | Lines |
|------|---------|-------|
| `apps/api/schemas/validators.py` | Security patterns and validation functions | ~80 |
| `apps/api/schemas/requests/__init__.py` | Package docstring | ~12 |
| `apps/api/schemas/requests/config.py` | 8 config schemas | ~200 |
| `apps/api/schemas/requests/query.py` | QueryRequest with 30 fields | ~180 |
| `apps/api/schemas/requests/sessions.py` | 3 session schemas | ~60 |
| `apps/api/schemas/requests/control.py` | 2 control schemas | ~50 |

### Test Files Created
| File | Tests |
|------|-------|
| `tests/unit/test_validators.py` | 21 tests |
| `tests/unit/test_request_config_schemas.py` | 25 tests |
| `tests/unit/test_request_query_schema.py` | 15 tests |
| `tests/unit/test_request_sessions_schema.py` | 7 tests |
| `tests/unit/test_request_control_schema.py` | 4 tests |

### Updated (Task 7-8, Post-plan)
- `apps/api/routes/query.py` - Direct import from `requests.query`
- `apps/api/routes/websocket.py` - Direct import from `requests.query`
- `apps/api/routes/session_control.py` - Imports from multiple submodules
- `apps/api/routes/checkpoints.py` - Direct import from `requests.control`
- `apps/api/routes/interactions.py` - Direct import from `requests.sessions`
- `apps/api/services/webhook.py` - Direct import from `requests.config`
- `apps/api/services/agent/service.py` - TYPE_CHECKING imports updated
- `apps/api/services/agent/hooks.py` - TYPE_CHECKING imports updated
- 13 test files updated with direct submodule imports

### Deleted (Task 9)
- `apps/api/schemas/requests_old.py` - Original 653-line monolithic file

## Commands Executed

```bash
# Test verification (ran multiple times)
uv run pytest tests/unit/ -q
# Result: 351 passed

# Type checking
uv run mypy apps/api --strict
# Result: Success: no issues found in 55 source files

# Linting
uv run ruff check apps/api/schemas/
# Result: All checks passed

# Import verification
uv run python -c "from apps.api.schemas.requests.query import QueryRequest; print('OK')"
# Result: OK
```

## Verification Results

| Check | Result |
|-------|--------|
| Unit tests | 351 passed |
| Integration tests | 123 passed, 6 skipped |
| mypy --strict | Success (55 files) |
| ruff check | Passed |
| No stale references | Confirmed |

## Import Pattern Reference

```python
# Query requests
from apps.api.schemas.requests.query import QueryRequest

# Config schemas
from apps.api.schemas.requests.config import (
    HooksConfigSchema,
    HookWebhookSchema,
    McpServerConfigSchema,
    AgentDefinitionSchema,
    OutputFormatSchema,
    SandboxSettingsSchema,
    SdkPluginConfigSchema,
    ImageContentSchema,
)

# Session schemas
from apps.api.schemas.requests.sessions import (
    ResumeRequest,
    ForkRequest,
    AnswerRequest,
)

# Control schemas
from apps.api.schemas.requests.control import (
    ControlRequest,
    RewindRequest,
)

# Security validators
from apps.api.schemas.validators import (
    validate_no_null_bytes,
    validate_no_path_traversal,
    validate_url_not_internal,
    validate_tool_name,
    validate_model_name,
)
```

## Next Steps

1. Consider similar refactoring for `responses.py` if it grows large
2. Monitor for any import issues in CI/CD pipelines
3. Update API documentation if external consumers exist

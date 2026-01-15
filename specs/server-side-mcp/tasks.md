---
spec: server-side-mcp
phase: tasks
total_tasks: 46
created: 2026-01-15T17:10:00Z
---

# Implementation Tasks: Server-Side MCP Configuration

## Phase 1: Make It Work (POC)

Focus: Validate the three-tier configuration merge works end-to-end. Skip comprehensive tests, accept basic validation only.

### 1.1 File Loading POC

- [x] 1.1 Create basic config loader with file reading
  - **Do**: Create `apps/api/services/mcp_config_loader.py` with `McpConfigLoader` class. Implement `load_application_config()` that reads `.mcp-server-config.json` from project root, parses JSON, returns dict. Handle missing file by returning empty dict and logging warning.
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: Can read JSON file, parse mcpServers section, return dict of server configs
  - **Verify**: Create test file `.mcp-server-config.json` in project root, manually run `python -c "from apps.api.services.mcp_config_loader import McpConfigLoader; print(McpConfigLoader().load_application_config())"` and verify dict returned
  - **Commit**: `feat(mcp): add basic config file loader`
  - _Requirements: AC-1.1, AC-1.2_
  - _Design: McpConfigLoader component_

- [x] 1.2 Add environment variable resolution to config loader
  - **Do**: Add `resolve_env_vars(config: dict[str, object]) -> dict[str, object]` method. Use regex pattern `\$\{([A-Z_][A-Z0-9_]*)\}` to find placeholders. Replace with `os.environ.get(var_name)`, leave placeholder if not found. Recursively process nested dicts and lists.
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: Environment variables like `${GITHUB_TOKEN}` are replaced with actual values from server environment
  - **Verify**: Set `export TEST_TOKEN=secret123`, create config with `"token": "${TEST_TOKEN}"`, verify resolution works
  - **Commit**: `feat(mcp): add env var resolution to config loader`
  - _Requirements: AC-1.4, FR-2_
  - _Design: Environment Variable Resolution_

- [x] 1.3 [VERIFY] Quality checkpoint: `uv run ruff check apps/api/services/mcp_config_loader.py && uv run ty check`
  - **Do**: Run lint and type check on new config loader module
  - **Verify**: Both commands exit 0 with no errors
  - **Done when**: No lint errors, no type errors
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 1.2 Database Integration POC

- [x] 1.4 Extend McpServerConfigService with API-key scoping
  - **Do**: Modify `apps/api/services/mcp_server_configs.py`. Change `_server_key(name: str)` to `_server_key(api_key: str, name: str)` returning `f"mcp_server:{api_key}:{name}"`. Add `_index_key(api_key: str)` returning `f"mcp_servers:index:{api_key}"`. Add `list_servers_for_api_key(api_key: str)` that scans keys with pattern. Update existing methods to accept `api_key` parameter.
  - **Files**: `apps/api/services/mcp_server_configs.py`
  - **Done when**: Redis keys include api_key scope, list/create/update/delete methods accept api_key parameter
  - **Verify**: Manually test in Python REPL with different API keys, verify isolation
  - **Commit**: `feat(mcp): add api-key scoping to mcp server storage`
  - _Requirements: AC-2.1, AC-2.2, AC-2.3, FR-3_
  - _Design: McpServerConfigService (EXTENDED)_

- [x] 1.5 Update MCP server routes with API-key filtering
  - **Do**: Modify `apps/api/routes/mcp_servers.py`. Update `list_mcp_servers()` to call `list_servers_for_api_key(api_key)`. Update `create_mcp_server()` to call `create_server_for_api_key(api_key, ...)`. Update other CRUD operations to filter by api_key.
  - **Files**: `apps/api/routes/mcp_servers.py`
  - **Done when**: All endpoints filtered by authenticated API key from header
  - **Verify**: `curl -H "X-API-Key: test-key" http://localhost:54000/api/v1/mcp-servers` returns only that key's servers
  - **Commit**: `feat(mcp): filter mcp endpoints by api key`
  - _Requirements: AC-2.5, AC-2.6_
  - _Design: Route-Level Filtering_

- [x] 1.6 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check`
  - **Do**: Run quality checks on modified services and routes
  - **Verify**: All commands exit 0
  - **Done when**: No lint errors, no type errors
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 1.3 Merge Logic POC

- [x] 1.7 Implement basic config merge in loader
  - **Do**: Add `merge_configs(application: dict, api_key: dict, request: dict | None) -> dict` method to `McpConfigLoader`. If `request == {}`, return empty dict (opt-out). If `request is None`, merge application and api_key. If request has values, merge all three. Same-name servers from higher tier completely replace lower tier (dict update, not deep merge).
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: Merge precedence works: Application < API-Key < Request
  - **Verify**: Write simple test script that verifies merge logic with example dicts
  - **Commit**: `feat(mcp): implement three-tier config merge`
  - _Requirements: AC-3.1, AC-3.2, AC-3.4, AC-3.5, FR-4_
  - _Design: Configuration Merge Strategy_

- [x] 1.8 Create config injector service
  - **Do**: Create `apps/api/services/mcp_config_injector.py` with `McpConfigInjector` class. Implement `inject(request: QueryRequest, api_key: str) -> QueryRequest` that loads configs via loader, merges them, updates request.mcp_servers field, returns enriched request. Handle opt-out case (empty dict).
  - **Files**: `apps/api/services/mcp_config_injector.py`
  - **Done when**: Takes request, returns enriched request with merged MCP servers
  - **Verify**: Manually test in Python REPL with sample QueryRequest
  - **Commit**: `feat(mcp): add config injector service`
  - _Requirements: AC-1.7, AC-3.3, FR-5_
  - _Design: McpConfigInjector component_

- [x] 1.9 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check`
  - **Do**: Run quality checks on new injector and updated loader
  - **Verify**: All commands exit 0
  - **Done when**: No lint errors, no type errors
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 1.4 Integration POC

- [x] 1.10 Wire config injector into AgentService
  - **Do**: Modify `apps/api/services/agent/service.py`. Add `McpConfigInjector` as dependency in `__init__`. In `query_stream()` method, call `enriched_request = await self.mcp_injector.inject(request, api_key)` BEFORE `OptionsBuilder(enriched_request).build()`. Update all query methods similarly.
  - **Files**: `apps/api/services/agent/service.py`
  - **Done when**: All query methods inject server-side MCP before SDK execution
  - **Verify**: Add print statement in inject method, run query via API, verify injection happens
  - **Commit**: `feat(mcp): integrate injector into agent service`
  - _Requirements: FR-5_
  - _Design: Integration Point_

- [x] 1.11 Add DI providers for new services
  - **Do**: Create dependency provider functions in `apps/api/dependencies.py` for `get_mcp_config_loader()` and `get_mcp_config_injector()`. Follow existing DI patterns with Protocol-based abstractions.
  - **Files**: `apps/api/dependencies.py`
  - **Done when**: FastAPI can inject loader and injector into routes/services
  - **Verify**: Start server, verify no DI errors at startup
  - **Commit**: `feat(mcp): add di providers for mcp config services`
  - _Design: Dependency Injection Pattern_

- [x] 1.12 Create example config file
  - **Do**: Create `.mcp-server-config.json.example` in project root with three example servers (stdio github, stdio postgres, sse slack). Include comments via JSON-compatible structure. Document `${VAR}` placeholder syntax. Set slack to `enabled: false` to show disabled example.
  - **Files**: `.mcp-server-config.json.example`
  - **Done when**: Example file demonstrates all transport types and env var usage
  - **Verify**: Copy to `.mcp-server-config.json`, start app, verify config loads
  - **Commit**: `docs(mcp): add example server-side config file`
  - _Requirements: AC-1.2, AC-1.3_
  - _Design: Configuration File Format_

- [x] 1.13 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check`
  - **Do**: Run quality checks on all modified files
  - **Verify**: All commands exit 0
  - **Done when**: No lint errors, no type errors
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

- [x] 1.14 POC Checkpoint - Manual E2E test
  - **Do**: Manually test complete flow: (1) Create `.mcp-server-config.json` with test server, (2) Create API key in Redis, (3) Add server via `/mcp-servers` for that key, (4) Send query request with null mcp_servers, (5) Verify server-side configs injected, (6) Send request with empty dict, verify opt-out works
  - **Done when**: Three-tier merge works end-to-end from file → database → request
  - **Verify**: Manual testing with curl commands, check logs for merged config
  - **Commit**: `feat(mcp): complete poc implementation`
  - **RESULT**: BLOCKER FOUND - `get_agent_service()` doesn't pass `mcp_config_injector` to `AgentService()`. Must fix before Phase 2.

## Phase 2: TDD Implementation

After POC validated, write comprehensive tests FIRST (RED), then ensure implementation passes (GREEN), then refactor.

### 2.1 Config Loader Tests (TDD: RED-GREEN-REFACTOR)

- [x] 2.1 [RED] Write failing tests for application config loading
  - **Do**: Create `tests/unit/services/test_mcp_config_loader.py`. Write test functions: `test_load_application_config_success()` (reads valid file), `test_load_application_config_missing_file()` (returns empty dict), `test_load_application_config_malformed_json()` (logs warning, returns empty dict), `test_load_application_config_caching()` (verify single file read). Tests should FAIL initially.
  - **Files**: `tests/unit/services/test_mcp_config_loader.py`
  - **Done when**: All 4 tests written and FAILING (RED phase complete)
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py::test_load_application_config_success -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for config loading`
  - _Requirements: AC-1.1, AC-1.5, AC-1.6_
  - _Design: Test Strategy - Unit Tests_

- [x] 2.2 [GREEN] Make config loading tests pass
  - **Do**: Update `McpConfigLoader.load_application_config()` to pass all tests. Add file caching with `functools.lru_cache`. Handle missing file gracefully. Catch JSON parse errors and log warnings. Add structured logging.
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: All 4 tests PASS (GREEN phase complete)
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -k load_application -v` shows all PASSED
  - **Commit**: `feat(mcp): implement robust config file loading`
  - _Requirements: AC-1.1, AC-1.5, AC-1.6_

- [x] 2.3 [RED] Write failing tests for env var resolution
  - **Do**: Add test functions: `test_resolve_env_vars_success()` (resolves `${VAR}`), `test_resolve_env_vars_missing_var()` (leaves placeholder, logs warning), `test_resolve_env_vars_nested_objects()` (deep resolution in nested dicts), `test_resolve_env_vars_in_arrays()` (resolution in list items). Mock `os.environ` in tests. Tests should FAIL.
  - **Files**: `tests/unit/services/test_mcp_config_loader.py`
  - **Done when**: All env var tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -k resolve_env -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for env var resolution`
  - _Requirements: AC-1.4, FR-2_

- [x] 2.4 [GREEN] Make env var resolution tests pass
  - **Do**: Update `McpConfigLoader.resolve_env_vars()` to handle all test cases. Add recursive traversal for nested structures. Add logging for missing vars. Handle edge cases (non-string values, already-resolved, etc).
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: All env var tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -k resolve_env -v` shows all PASSED
  - **Commit**: `feat(mcp): implement recursive env var resolution`
  - _Requirements: AC-1.4, FR-2_

- [x] 2.5 [REFACTOR] Clean up config loader implementation
  - **Do**: Extract helper methods for JSON parsing, validation, caching. Add comprehensive docstrings (Google style). Improve error messages. Add type hints for all internal methods. Keep tests green throughout.
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: Code is cleaner, tests still pass, no functional changes
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -v` still all PASSED
  - **Commit**: `refactor(mcp): clean up config loader implementation`

- [x] 2.6 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check && uv run pytest tests/unit/services/test_mcp_config_loader.py`
  - **Do**: Run quality checks and verify all config loader tests pass
  - **Verify**: All commands exit 0
  - **Done when**: Lint clean, types clean, tests green
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 2.2 Merge Logic Tests (TDD: RED-GREEN-REFACTOR)

- [x] 2.7 [RED] Write failing tests for config merge precedence
  - **Do**: Add test functions: `test_merge_configs_request_overrides_all()` (request tier highest), `test_merge_configs_api_key_overrides_application()` (api-key tier middle), `test_merge_configs_empty_request_opts_out()` (empty dict disables all), `test_merge_configs_null_request_uses_defaults()` (null = merge server-side), `test_merge_configs_complete_replacement()` (not deep merge). Tests should FAIL.
  - **Files**: `tests/unit/services/test_mcp_config_loader.py`
  - **Done when**: All 5 merge tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -k merge -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for config merge`
  - _Requirements: AC-3.1, AC-3.2, AC-3.4, AC-3.5, FR-4_

- [x] 2.8 [GREEN] Make merge precedence tests pass
  - **Do**: Update `McpConfigLoader.merge_configs()` to pass all tests. Implement correct precedence order. Handle opt-out case explicitly. Ensure replacement semantics (not deep merge). Add assertions for invalid inputs.
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: All 5 merge tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -k merge -v` shows all PASSED
  - **Commit**: `feat(mcp): implement correct merge precedence`
  - _Requirements: AC-3.1, AC-3.2, AC-3.4, AC-3.5, FR-4_

- [x] 2.9 [REFACTOR] Optimize merge logic
  - **Do**: Simplify merge implementation using dict unpacking. Add inline comments explaining precedence. Extract opt-out logic to separate method. Keep tests green.
  - **Files**: `apps/api/services/mcp_config_loader.py`
  - **Done when**: Merge code is clearer, tests still pass
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_loader.py -k merge -v` still all PASSED
  - **Commit**: `refactor(mcp): simplify merge logic`

- [x] 2.10 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check && uv run pytest tests/unit/services/test_mcp_config_loader.py`
  - **Do**: Run full quality suite on config loader
  - **Verify**: All commands exit 0
  - **Done when**: Lint clean, types clean, all config loader tests green
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 2.3 Security Validator Tests (TDD: RED-GREEN-REFACTOR)

- [x] 2.11 [RED] Write failing tests for command injection detection
  - **Do**: Create `tests/unit/services/test_mcp_config_validator.py`. Write test functions: `test_validate_command_injection_detected()` (reject shell metacharacters), `test_validate_command_injection_safe_command()` (allow safe commands), `test_validate_command_injection_null()` (handle None gracefully). Use existing `SHELL_METACHAR_PATTERN` from `apps/api/schemas/validators.py`. Tests should FAIL.
  - **Files**: `tests/unit/services/test_mcp_config_validator.py`
  - **Done when**: All command injection tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -k command_injection -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for command injection`
  - _Requirements: AC-4.3, FR-9_
  - _Design: Security Validation_

- [x] 2.12 [GREEN] Implement command injection validator
  - **Do**: Create `apps/api/services/mcp_config_validator.py` with `ConfigValidator` class. Implement `validate_command_injection(command: str | None)` using `SHELL_METACHAR_PATTERN`. Raise `ValueError` with clear message if metacharacters found. Import from existing validators module.
  - **Files**: `apps/api/services/mcp_config_validator.py`
  - **Done when**: All command injection tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -k command_injection -v` shows all PASSED
  - **Commit**: `feat(mcp): implement command injection validator`
  - _Requirements: AC-4.3, FR-9_

- [x] 2.13 [RED] Write failing tests for SSRF prevention
  - **Do**: Add test functions: `test_validate_ssrf_internal_ip()` (reject 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), `test_validate_ssrf_localhost()` (reject localhost/127.0.0.1), `test_validate_ssrf_metadata_endpoint()` (reject 169.254.169.254), `test_validate_ssrf_link_local()` (reject link-local), `test_validate_ssrf_valid_url()` (allow public URLs), `test_validate_ssrf_null()` (handle None). Tests should FAIL.
  - **Files**: `tests/unit/services/test_mcp_config_validator.py`
  - **Done when**: All SSRF tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -k ssrf -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for ssrf prevention`
  - _Requirements: AC-4.4, FR-9_

- [x] 2.14 [GREEN] Implement SSRF validator
  - **Do**: Add `validate_ssrf(url: str | None)` method to `ConfigValidator`. Use existing `validate_url_not_internal()` from `apps/api/schemas/validators.py`. Handle None gracefully. Raise `ValueError` for internal URLs.
  - **Files**: `apps/api/services/mcp_config_validator.py`
  - **Done when**: All SSRF tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -k ssrf -v` shows all PASSED
  - **Commit**: `feat(mcp): implement ssrf prevention validator`
  - _Requirements: AC-4.4, FR-9_

- [ ] 2.15 [RED] Write failing tests for credential sanitization
  - **Do**: Add test functions: `test_sanitize_credentials_env_vars()` (redact sensitive env keys), `test_sanitize_credentials_headers()` (redact auth headers), `test_sanitize_credentials_preserves_safe_fields()` (don't redact command, type, etc), `test_sanitize_credentials_nested()` (deep sanitization). Tests should FAIL.
  - **Files**: `tests/unit/services/test_mcp_config_validator.py`
  - **Done when**: All sanitization tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -k sanitize -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for credential sanitization`
  - _Requirements: AC-4.2, FR-8_

- [ ] 2.16 [GREEN] Implement credential sanitizer
  - **Do**: Add `sanitize_credentials(config: dict[str, object]) -> dict[str, object]` method. Define `SENSITIVE_PATTERNS = ["api_key", "apikey", "secret", "password", "token", "auth", "credential", "authorization"]`. Replace matching keys with `"***REDACTED***"`. Handle nested dicts recursively.
  - **Files**: `apps/api/services/mcp_config_validator.py`
  - **Done when**: All sanitization tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -k sanitize -v` shows all PASSED
  - **Commit**: `feat(mcp): implement credential sanitization`
  - _Requirements: AC-4.2, FR-8_

- [ ] 2.17 [REFACTOR] Add comprehensive validator
  - **Do**: Add `validate_config(config: dict[str, object])` method that calls all validators (command injection, SSRF, null bytes). Add Google-style docstrings to all methods. Keep tests green.
  - **Files**: `apps/api/services/mcp_config_validator.py`
  - **Done when**: Single entry point for validation, all tests still pass
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_validator.py -v` all PASSED
  - **Commit**: `refactor(mcp): add comprehensive validator method`

- [ ] 2.18 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check && uv run pytest tests/unit/services/test_mcp_config_validator.py`
  - **Do**: Run quality checks on validator
  - **Verify**: All commands exit 0
  - **Done when**: Lint clean, types clean, all validator tests green
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 2.4 Config Injector Tests (TDD: RED-GREEN-REFACTOR)

- [ ] 2.19 [RED] Write failing tests for config injection
  - **Do**: Create `tests/unit/services/test_mcp_config_injector.py`. Write test functions: `test_inject_with_null_request_mcp_servers()` (uses server-side), `test_inject_with_empty_dict_opts_out()` (returns unchanged), `test_inject_logs_sanitized_config()` (verify logging), `test_inject_with_request_override()` (preserves request config). Mock loader and validator dependencies. Tests should FAIL.
  - **Files**: `tests/unit/services/test_mcp_config_injector.py`
  - **Done when**: All injector tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_injector.py -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for config injector`
  - _Requirements: AC-3.5, AC-3.6, FR-5_

- [ ] 2.20 [GREEN] Make config injector tests pass
  - **Do**: Update `McpConfigInjector.inject()` to pass all tests. Add structured logging with sanitized config. Handle opt-out case explicitly. Coordinate loader and validator calls properly.
  - **Files**: `apps/api/services/mcp_config_injector.py`
  - **Done when**: All injector tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_injector.py -v` shows all PASSED
  - **Commit**: `feat(mcp): implement complete config injection`
  - _Requirements: AC-3.5, AC-3.6, FR-5_

- [ ] 2.21 [REFACTOR] Add error handling to injector
  - **Do**: Add try-catch blocks for loader/validator errors. Log errors with correlation IDs. Return original request if injection fails (graceful degradation). Keep tests green.
  - **Files**: `apps/api/services/mcp_config_injector.py`
  - **Done when**: Error handling robust, tests still pass
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_config_injector.py -v` all PASSED
  - **Commit**: `refactor(mcp): add error handling to injector`

- [ ] 2.22 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check && uv run pytest tests/unit/services/test_mcp_config_injector.py`
  - **Do**: Run quality checks on injector
  - **Verify**: All commands exit 0
  - **Done when**: Lint clean, types clean, all injector tests green
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 2.5 API-Key Scoping Tests (TDD: RED-GREEN-REFACTOR)

- [ ] 2.23 [RED] Write failing tests for API-key scoped storage
  - **Do**: Create `tests/unit/services/test_mcp_server_configs_scoped.py`. Write test functions: `test_server_key_includes_api_key()` (pattern check), `test_list_servers_for_api_key_isolation()` (no cross-tenant access), `test_create_server_for_api_key()` (scoped creation), `test_index_key_scoped()` (index pattern). Tests should FAIL due to signature changes.
  - **Files**: `tests/unit/services/test_mcp_server_configs_scoped.py`
  - **Done when**: All scoping tests written and FAILING
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_server_configs_scoped.py -v` shows FAILED
  - **Commit**: `test(mcp): add failing tests for api-key scoping`
  - _Requirements: AC-2.2, AC-2.3, FR-3_

- [ ] 2.24 [GREEN] Update service to pass scoping tests
  - **Do**: Ensure `McpServerConfigService` method signatures and implementations match test expectations. Fix any bugs found by tests. Ensure Redis key patterns correct.
  - **Files**: `apps/api/services/mcp_server_configs.py`
  - **Done when**: All scoping tests PASS
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_server_configs_scoped.py -v` shows all PASSED
  - **Commit**: `feat(mcp): complete api-key scoping implementation`
  - _Requirements: AC-2.2, AC-2.3, FR-3_

- [ ] 2.25 [REFACTOR] Extract key generation logic
  - **Do**: Extract `_server_key()` and `_index_key()` methods to separate key builder helper. Add validation for api_key format. Keep tests green.
  - **Files**: `apps/api/services/mcp_server_configs.py`
  - **Done when**: Key generation centralized, tests still pass
  - **Verify**: `uv run pytest tests/unit/services/test_mcp_server_configs_scoped.py -v` all PASSED
  - **Commit**: `refactor(mcp): centralize redis key generation`

- [ ] 2.26 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check && uv run pytest tests/unit/services/test_mcp_server_configs_scoped.py`
  - **Do**: Run quality checks on updated service
  - **Verify**: All commands exit 0
  - **Done when**: Lint clean, types clean, all scoping tests green
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

## Phase 3: Integration & Contract Tests

End-to-end validation with real services, backward compatibility verification.

### 3.1 Integration Tests

- [ ] 3.1 Write integration test for application config injection
  - **Do**: Create `tests/integration/test_server_side_mcp.py`. Write `test_application_mcp_servers_injected_into_query()` that creates `.mcp-server-config.json`, sends query with null mcp_servers, verifies server-side configs injected into SDK options. Use real file system and Redis.
  - **Files**: `tests/integration/test_server_side_mcp.py`
  - **Done when**: Test verifies application-level injection works end-to-end
  - **Verify**: `uv run pytest tests/integration/test_server_side_mcp.py::test_application_mcp_servers_injected_into_query -v` shows PASSED
  - **Commit**: `test(mcp): add integration test for application config`
  - _Requirements: AC-1.7_

- [ ] 3.2 Write integration test for API-key override
  - **Do**: Add `test_api_key_mcp_overrides_application()` that creates application config with server A, creates API-key config with server A (different settings), verifies API-key version used.
  - **Files**: `tests/integration/test_server_side_mcp.py`
  - **Done when**: Test verifies API-key tier overrides application tier
  - **Verify**: `uv run pytest tests/integration/test_server_side_mcp.py::test_api_key_mcp_overrides_application -v` shows PASSED
  - **Commit**: `test(mcp): add integration test for api-key override`
  - _Requirements: AC-2.4_

- [ ] 3.3 Write integration test for request override
  - **Do**: Add `test_request_mcp_servers_override_all()` that sets up application and API-key configs, sends request with mcp_servers dict, verifies request config used exclusively.
  - **Files**: `tests/integration/test_server_side_mcp.py`
  - **Done when**: Test verifies request tier has highest priority
  - **Verify**: `uv run pytest tests/integration/test_server_side_mcp.py::test_request_mcp_servers_override_all -v` shows PASSED
  - **Commit**: `test(mcp): add integration test for request override`
  - _Requirements: AC-3.1_

- [ ] 3.4 Write integration test for opt-out mechanism
  - **Do**: Add `test_opt_out_mechanism_disables_server_side_mcp()` that sets up server-side configs, sends request with `mcp_servers: {}`, verifies no MCP servers injected.
  - **Files**: `tests/integration/test_server_side_mcp.py`
  - **Done when**: Test verifies empty dict disables all server-side configs
  - **Verify**: `uv run pytest tests/integration/test_server_side_mcp.py::test_opt_out_mechanism_disables_server_side_mcp -v` shows PASSED
  - **Commit**: `test(mcp): add integration test for opt-out`
  - _Requirements: AC-3.4, FR-7_

- [ ] 3.5 Write integration test for multi-tenant isolation
  - **Do**: Add `test_api_key_isolation()` that creates servers for two different API keys, verifies each key only sees its own servers, cross-tenant access impossible.
  - **Files**: `tests/integration/test_server_side_mcp.py`
  - **Done when**: Test verifies zero data leakage between tenants
  - **Verify**: `uv run pytest tests/integration/test_server_side_mcp.py::test_api_key_isolation -v` shows PASSED
  - **Commit**: `test(mcp): add integration test for tenant isolation`
  - _Requirements: AC-2.3, NFR-8_

- [ ] 3.6 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check && uv run pytest tests/integration/test_server_side_mcp.py`
  - **Do**: Run quality checks and all integration tests
  - **Verify**: All commands exit 0
  - **Done when**: All integration tests green
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 3.2 Contract Tests

- [ ] 3.7 Write contract test for backward compatibility
  - **Do**: Create `tests/contract/test_server_side_mcp_contract.py`. Write `test_existing_query_tests_pass_unchanged()` that runs subset of existing query tests (from `tests/integration/test_agent_service.py`) to verify no breaking changes. Import and re-run existing test functions.
  - **Files**: `tests/contract/test_server_side_mcp_contract.py`
  - **Done when**: Test verifies existing functionality unchanged
  - **Verify**: `uv run pytest tests/contract/test_server_side_mcp_contract.py::test_existing_query_tests_pass_unchanged -v` shows PASSED
  - **Commit**: `test(mcp): add contract test for backward compatibility`
  - _Requirements: AC-3.3, NFR-7_

- [ ] 3.8 Write contract test for OpenAI compatibility
  - **Do**: Add `test_openai_endpoint_includes_server_side_mcp()` that sets up application config, sends request to `/v1/chat/completions`, verifies server-side MCP servers accessible (check logs or response metadata).
  - **Files**: `tests/contract/test_server_side_mcp_contract.py`
  - **Done when**: Test verifies OpenAI endpoint gets server-side configs
  - **Verify**: `uv run pytest tests/contract/test_server_side_mcp_contract.py::test_openai_endpoint_includes_server_side_mcp -v` shows PASSED
  - **Commit**: `test(mcp): add contract test for openai compatibility`
  - _Requirements: AC-5.1, AC-5.2_

- [ ] 3.9 [VERIFY] Quality checkpoint: `uv run pytest tests/contract/test_server_side_mcp_contract.py`
  - **Do**: Run all contract tests
  - **Verify**: All tests pass
  - **Done when**: 100% backward compatibility verified
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 3.3 Security Tests

- [ ] 3.10 Write security test for credential isolation
  - **Do**: Create `tests/security/test_server_side_mcp_security.py`. Write `test_application_config_env_vars_not_leaked()` that sets up config with `${SECRET}`, queries `/mcp-servers`, verifies response has `***REDACTED***` not actual value.
  - **Files**: `tests/security/test_server_side_mcp_security.py`
  - **Done when**: Test verifies credentials never leaked in API responses
  - **Verify**: `uv run pytest tests/security/test_server_side_mcp_security.py::test_application_config_env_vars_not_leaked -v` shows PASSED
  - **Commit**: `test(mcp): add security test for credential leakage`
  - _Requirements: AC-4.1, AC-4.2, FR-8_

- [ ] 3.11 Write security test for command injection
  - **Do**: Add `test_command_injection_rejected()` that attempts to create MCP server with command containing `; rm -rf /`, verifies rejection with 400 Bad Request.
  - **Files**: `tests/security/test_server_side_mcp_security.py`
  - **Done when**: Test verifies shell metacharacters blocked
  - **Verify**: `uv run pytest tests/security/test_server_side_mcp_security.py::test_command_injection_rejected -v` shows PASSED
  - **Commit**: `test(mcp): add security test for command injection`
  - _Requirements: AC-4.3, FR-9_

- [ ] 3.12 Write security test for SSRF prevention
  - **Do**: Add `test_ssrf_attempts_blocked()` that attempts to create MCP server with URL `http://169.254.169.254/latest/meta-data/`, verifies rejection.
  - **Files**: `tests/security/test_server_side_mcp_security.py`
  - **Done when**: Test verifies internal URLs blocked
  - **Verify**: `uv run pytest tests/security/test_server_side_mcp_security.py::test_ssrf_attempts_blocked -v` shows PASSED
  - **Commit**: `test(mcp): add security test for ssrf prevention`
  - _Requirements: AC-4.4, FR-9_

- [ ] 3.13 [VERIFY] Quality checkpoint: `uv run pytest tests/security/test_server_side_mcp_security.py`
  - **Do**: Run all security tests
  - **Verify**: All tests pass
  - **Done when**: Zero security vulnerabilities found
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

## Phase 4: Quality Gates

Final polish, comprehensive verification, documentation.

### 4.1 Coverage & Type Safety

- [ ] 4.1 Verify test coverage meets 90% target
  - **Do**: Run `uv run pytest --cov=apps/api/services/mcp_config_loader --cov=apps/api/services/mcp_config_injector --cov=apps/api/services/mcp_config_validator --cov-report=term-missing`. Review uncovered lines, add tests to reach 90%+.
  - **Files**: `tests/unit/services/test_mcp_config_*.py`
  - **Done when**: Coverage report shows ≥90% for all new services
  - **Verify**: Coverage output shows 90%+ line coverage
  - **Commit**: `test(mcp): increase coverage to 90%` (if new tests added)
  - _Requirements: NFR-3_

- [ ] 4.2 Run full type check with strict mode
  - **Do**: Run `uv run ty check` on entire codebase. Fix any type errors in new code. Ensure zero `Any` types used (except unavoidable external library types).
  - **Files**: Various MCP-related files
  - **Done when**: `ty check` exits 0 with no warnings on new code
  - **Verify**: `uv run ty check` output shows 0 errors for new modules
  - **Commit**: `fix(mcp): resolve type check warnings`
  - _Requirements: NFR-4_

- [ ] 4.3 Run full lint with auto-fix
  - **Do**: Run `uv run ruff check . --fix` to auto-fix issues. Run `uv run ruff format .` to format code. Manually review any unfixable issues.
  - **Files**: Various MCP-related files
  - **Done when**: `ruff check .` exits 0 with no warnings
  - **Verify**: `uv run ruff check .` shows 0 issues
  - **Commit**: `style(mcp): apply ruff formatting and fixes`

- [ ] 4.4 [VERIFY] Full local CI: `uv run ruff check . && uv run ty check --exit-zero && uv run pytest --cov=apps/api --cov-report=term-missing`
  - **Do**: Run complete local CI suite that matches GitHub Actions
  - **Verify**: All commands pass
  - **Done when**: Build succeeds, all tests pass, coverage ≥90%
  - **Commit**: `chore(mcp): pass local ci` (if fixes needed)

### 4.2 Documentation

- [ ] 4.5 Add Google-style docstrings to all public functions
  - **Do**: Review all new services (`mcp_config_loader.py`, `mcp_config_injector.py`, `mcp_config_validator.py`) and ensure every public function/class has Google-style docstring with Args, Returns, Raises sections. Include examples where helpful.
  - **Files**: `apps/api/services/mcp_config_*.py`
  - **Done when**: All public APIs documented with comprehensive docstrings
  - **Verify**: Manual review shows 100% docstring coverage for public APIs
  - **Commit**: `docs(mcp): add comprehensive docstrings`
  - _Requirements: NFR-10_

- [ ] 4.6 Update CLAUDE.md with server-side MCP usage
  - **Do**: Add "Server-Side MCP Configuration" section to `CLAUDE.md`. Document three-tier system, config file format, API-key scoping, opt-out mechanism. Include example `.mcp-server-config.json` snippet. Reference related specs.
  - **Files**: `CLAUDE.md`
  - **Done when**: Documentation explains how to use server-side MCP configs
  - **Verify**: Manual review of documentation section
  - **Commit**: `docs(mcp): document server-side config in claude.md`

- [ ] 4.7 Update openai-api spec with server-side MCP integration
  - **Do**: Add note to `specs/openai-api/decisions.md` explaining that OpenAI endpoints now have access to server-side MCP servers automatically. Document that Phase 2 tool calling will leverage these configs. Update any relevant diagrams.
  - **Files**: `specs/openai-api/decisions.md`
  - **Done when**: OpenAI spec documents server-side MCP availability
  - **Verify**: Manual review of updated spec
  - **Commit**: `docs(openai): document server-side mcp integration`

- [ ] 4.8 [VERIFY] Quality checkpoint: `uv run ruff check . && uv run ty check`
  - **Do**: Final quality check on documentation changes
  - **Verify**: All commands exit 0
  - **Done when**: No issues with doc files
  - **Commit**: `chore(mcp): pass quality checkpoint` (only if fixes needed)

### 4.3 Final Verification

- [ ] 4.9 Run full test suite with all markers
  - **Do**: Run `uv run pytest` (all tests), then `uv run pytest -m e2e` (e2e tests), verify 100% pass rate. Check for flaky tests.
  - **Files**: N/A
  - **Done when**: Full test suite passes reliably
  - **Verify**: `uv run pytest -v` shows all tests PASSED
  - **Commit**: None

- [ ] 4.10 Manual acceptance criteria verification
  - **Do**: Read `specs/server-side-mcp/requirements.md`. Manually verify each AC-X.Y is satisfied by implementation. Create checklist, mark each as verified.
  - **Files**: N/A
  - **Done when**: All 27 acceptance criteria verified as met
  - **Verify**: Manual review against requirements
  - **Commit**: None

- [ ] 4.11 [VERIFY] V1 Full local CI: `uv run ruff check . && uv run ty check --exit-zero && uv run pytest --cov=apps/api --cov-report=term-missing`
  - **Do**: Run complete local CI suite as final verification
  - **Verify**: All commands pass
  - **Done when**: Build succeeds, all tests pass
  - **Commit**: `chore(mcp): pass local ci` (if fixes needed)

- [ ] 4.12 [VERIFY] V2 CI pipeline passes
  - **Do**: Push feature branch, create PR, verify GitHub Actions CI passes. Check all jobs (lint, typecheck, tests, migrations).
  - **Verify**: `gh pr checks` shows all green
  - **Done when**: CI pipeline passes
  - **Commit**: None

- [ ] 4.13 [VERIFY] V3 AC checklist
  - **Do**: Read requirements.md, verify each AC-* is satisfied by final implementation
  - **Verify**: Manual review against implementation
  - **Done when**: All acceptance criteria confirmed met
  - **Commit**: None

## Notes

**POC shortcuts taken**:
- Phase 1 skips comprehensive error handling (basic logging only)
- Phase 1 uses simple dict operations (no optimization)
- Phase 1 minimal validation (just file read success)
- Phase 1 manual testing only (no automated tests)

**Production TODOs addressed in Phase 2+**:
- Comprehensive unit tests with ≥90% coverage
- Robust error handling with structured logging
- Security validation (command injection, SSRF, credential sanitization)
- Integration tests for multi-tier scenarios
- Contract tests for backward compatibility
- Performance optimization if needed

**TDD Methodology**:
- Phase 2 strictly follows RED-GREEN-REFACTOR cycle
- Tests written FIRST, implementation SECOND
- Each subsystem (loader, merger, validator, injector) has dedicated TDD section
- Refactor step ensures code quality while maintaining green tests

**Quality Checkpoints**:
- Inserted every 2-3 tasks in Phase 2 (TDD)
- Every 3 tasks in Phase 3 (Integration)
- Full CI simulation before final verification
- Final verification sequence in Phase 4.3

**Branch Management**:
- Already on feature branch `feat/openai-api` (from git status)
- May need to create new branch for this spec: `feat/server-side-mcp`
- Final PR will be created in task 4.12

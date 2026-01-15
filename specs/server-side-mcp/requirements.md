---
spec: server-side-mcp
phase: requirements
created: 2026-01-15T16:50:00Z
---

# Requirements: Server-Side MCP Server Configuration

## Goal

Enable automatic provisioning of MCP (Model Context Protocol) servers to all API requests through a three-tier configuration system (application-level file, per-API-key database storage, and per-request override), eliminating the need for clients to configure MCP servers manually while maintaining multi-tenant isolation and backward compatibility with existing per-request MCP configuration.

## User Stories

### US-1: Application-Level MCP Configuration File

**As a** system administrator
**I want to** define global MCP servers in a configuration file loaded at application startup
**So that** all API requests automatically have access to organization-wide MCP tools without per-request configuration

**Acceptance Criteria:**

- [ ] AC-1.1: Application loads `.mcp-server-config.json` from project root at startup (test: verify file read in TDD RED phase)
- [ ] AC-1.2: Configuration file follows standard MCP JSON format with `mcpServers` object (test: schema validation)
- [ ] AC-1.3: File supports stdio, SSE, and HTTP transport types (test: parse all three types)
- [ ] AC-1.4: Environment variable placeholders in config (e.g., `${GITHUB_TOKEN}`) are resolved at load time, not from user input (test: verify server-side-only resolution)
- [ ] AC-1.5: Invalid configuration logs warning and continues with empty config (no startup failure) (test: malformed JSON handling)
- [ ] AC-1.6: Configuration is cached in memory after first load (test: verify single file read)
- [ ] AC-1.7: Application-level servers are injected into all query requests automatically (test: verify presence in SDK options)

### US-2: Per-API-Key MCP Server Scoping

**As a** platform operator supporting multiple tenants
**I want to** assign different MCP servers to different API keys stored in the database
**So that** each tenant can have isolated tool access without cross-tenant data leakage

**Acceptance Criteria:**

- [ ] AC-2.1: Existing `McpServerConfigService` is extended to support API-key scoping (test: storage with api_key field)
- [ ] AC-2.2: Redis keys use pattern `mcp_server:{api_key}:{server_name}` for multi-tenancy (test: key format validation)
- [ ] AC-2.3: API key from `X-API-Key` header determines which database servers are loaded (test: isolation between API keys)
- [ ] AC-2.4: Database MCP servers override application-level servers with same name (test: merge precedence)
- [ ] AC-2.5: Listing MCP servers via `/mcp-servers` endpoint filters by authenticated API key (test: no cross-tenant visibility)
- [ ] AC-2.6: Creating MCP server via POST `/mcp-servers` associates with authenticated API key (test: api_key stored in record)

### US-3: Three-Tier Configuration Merge Strategy

**As a** API user
**I want to** specify per-request MCP servers that override server-side defaults
**So that** I can use request-specific tools while benefiting from pre-configured servers

**Acceptance Criteria:**

- [ ] AC-3.1: Merge order is Application < API-Key < Request (lowest to highest priority) (test: verify override chain)
- [ ] AC-3.2: MCP server with same name in higher tier completely replaces lower tier (not deep merge) (test: replacement semantics)
- [ ] AC-3.3: Per-request `mcp_servers` field continues to work unchanged (backward compatibility) (test: existing tests pass)
- [ ] AC-3.4: Empty `mcp_servers: {}` in request disables ALL server-side MCP servers (test: opt-out mechanism)
- [ ] AC-3.5: Null/absent `mcp_servers` in request uses merged server-side configs (test: default behavior)
- [ ] AC-3.6: Final merged config is logged with sanitized credentials (test: verify log output)

### US-4: Security and Validation

**As a** security engineer
**I want to** ensure server-side MCP configuration prevents credential leakage and command injection
**So that** the system remains secure in multi-tenant environments

**Acceptance Criteria:**

- [ ] AC-4.1: Application-level config resolves environment variables server-side only (test: `${VAR}` syntax)
- [ ] AC-4.2: Per-API-key configs stored in database have credentials sanitized in API responses (test: `***REDACTED***` in GET `/mcp-servers`)
- [ ] AC-4.3: Command injection validation applies to all config sources (test: reject shell metacharacters)
- [ ] AC-4.4: SSRF protection validates HTTP transport URLs (test: reject internal IPs)
- [ ] AC-4.5: Configuration file permissions warning if world-readable (test: file stat check)
- [ ] AC-4.6: TDD process: Write security test FIRST, then implement validation (test: RED-GREEN-REFACTOR cycle documented)

### US-5: OpenAI API Compatibility Integration

**As a** developer using the OpenAI-compatible endpoint
**I want to** automatically access server-side MCP tools in `/v1/chat/completions`
**So that** MCP tools are available without client-side configuration

**Acceptance Criteria:**

- [ ] AC-5.1: OpenAI endpoint requests include merged server-side MCP servers (test: verify in request translator)
- [ ] AC-5.2: Per-API-key scoping applies to OpenAI endpoints (test: tenant isolation)
- [ ] AC-5.3: MCP tools discovered via server-side config are callable in OpenAI requests (test: end-to-end tool execution)
- [ ] AC-5.4: Error responses use OpenAI error format when MCP server fails (test: error translation)
- [ ] AC-5.5: Tool calling in OpenAI API (Phase 2) will leverage these server-side MCP servers (test: placeholder for future integration)

## Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1 | Load `.mcp-server-config.json` from project root at startup | Must Have | File parsed with Pydantic schema, errors logged but not fatal |
| FR-2 | Resolve environment variables in application config at load time | Must Have | `${VAR}` syntax replaced with `os.environ.get()` values, never from user input |
| FR-3 | Store per-API-key MCP servers in Redis with key scoping | Must Have | Redis keys include api_key identifier, CRUD operations filtered by API key |
| FR-4 | Merge three configuration tiers with clear precedence | Must Have | Application < API-Key < Request, same-name servers replaced completely |
| FR-5 | Inject merged MCP config into `ClaudeAgentOptions` before SDK execution | Must Have | `OptionsBuilder` applies merge logic, logs final config |
| FR-6 | Extend `/mcp-servers` CRUD endpoints with API-key scoping | Must Have | List/create/update/delete filtered by authenticated API key |
| FR-7 | Support opt-out mechanism for server-side MCP servers | Should Have | Empty `mcp_servers: {}` in request disables all server-side configs |
| FR-8 | Sanitize credentials in API responses and logs | Must Have | `***REDACTED***` for env vars, headers, secrets in all outputs |
| FR-9 | Validate command injection and SSRF attacks | Must Have | Reject shell metacharacters, internal URLs, null bytes |
| FR-10 | Enable hot reload of application-level config (stretch goal) | Could Have | File watcher triggers config reload without restart |

## Non-Functional Requirements

| ID | Requirement | Metric | Target |
|----|-------------|--------|--------|
| NFR-1 | Configuration load performance | Startup time overhead | < 100ms for config parsing |
| NFR-2 | Redis query performance | Per-request overhead | < 10ms for API-key scoped lookup |
| NFR-3 | Test coverage | Line coverage | ≥ 90% for new MCP config services |
| NFR-4 | Type safety | `ty check` pass | Zero `Any` types, strict mode enabled |
| NFR-5 | TDD adherence | Development process | All features written RED-GREEN-REFACTOR (tests before implementation) |
| NFR-6 | Security validation | Vulnerability scans | Zero command injection, SSRF, or credential leakage |
| NFR-7 | Backward compatibility | Existing test suite | 100% of existing tests pass without modification |
| NFR-8 | Multi-tenant isolation | Cross-API-key access | Zero data leakage in integration tests |
| NFR-9 | Logging quality | Structured logs | All config operations logged with correlation IDs |
| NFR-10 | Documentation completeness | Inline docstrings | Google-style docstrings for all public functions |

## Glossary

- **MCP (Model Context Protocol)**: Standard protocol for connecting LLMs to external tools and data sources
- **MCP Server**: Process or service implementing MCP protocol (stdio, SSE, or HTTP transport)
- **Transport Type**: Communication method between API and MCP server (stdio=subprocess, SSE=Server-Sent Events, HTTP=JSON-RPC)
- **Application-Level Config**: Global MCP servers defined in `.mcp-server-config.json` file
- **API-Key-Level Config**: Tenant-specific MCP servers stored in Redis database with API key scope
- **Request-Level Config**: Per-request MCP servers specified in `QueryRequest.mcp_servers` field (highest priority)
- **Merge Precedence**: Priority order for conflicting configurations (Application < API-Key < Request)
- **Credential Sanitization**: Redacting sensitive data (`***REDACTED***`) in API responses and logs
- **Environment Variable Resolution**: Server-side replacement of `${VAR}` placeholders with `os.environ` values
- **TDD (Test-Driven Development)**: Development methodology where tests are written before implementation code

## Out of Scope

- **MCP Tool Calling Translation**: Automatic translation of MCP tools to OpenAI function calling format (deferred to OpenAI API Phase 2)
- **MCP Server Lifecycle Management**: Automatic start/stop/restart of MCP server processes (managed by SDK)
- **Configuration UI**: Web interface for managing MCP servers (API-only in this phase)
- **Hot Reload**: Dynamic config reload without restart (stretch goal, not required)
- **Custom Transport Types**: Only stdio, SSE, and HTTP supported (MCP spec standard)
- **MCP Server Health Checks**: Proactive health monitoring and auto-recovery (SDK responsibility)
- **Configuration Versioning**: Git-style config history and rollback (future enhancement)
- **Global Filesystem Discovery**: `.claude.json` and `.mcp.json` discovery remains read-only (no auto-injection in this phase unless explicitly configured)

## Dependencies

- **Existing Infrastructure**:
  - `McpDiscoveryService` (filesystem MCP server discovery)
  - `McpServerConfigService` (Redis-backed database storage)
  - `OptionsBuilder` (converts API schemas to SDK options)
  - Pydantic validation schemas (`McpServerConfigSchema`)
  - Existing security validators (`SHELL_METACHAR_PATTERN`, `validate_url_not_internal`)

- **External Libraries** (already in project):
  - `pydantic-settings` (configuration management)
  - `structlog` (structured logging)
  - `redis` (cache/database backend)
  - `claude-agent-sdk` (MCP support built-in)

- **Configuration**:
  - `.mcp-server-config.json` file (new, optional)
  - Redis server (existing)
  - Environment variables for credentials (existing pattern)

- **Related Specs**:
  - `openai-api` (completed) - May require documentation update for server-side MCP availability

## Success Criteria

1. **Functional Success**:
   - Application-level `.mcp-server-config.json` loaded at startup with all MCP servers available to requests
   - Per-API-key MCP servers stored in Redis with complete tenant isolation (verified via integration tests)
   - Three-tier merge strategy working correctly with clear precedence (Application < API-Key < Request)
   - Backward compatibility: All existing tests pass without modification

2. **Test Coverage**:
   - ≥ 90% line coverage for new MCP configuration services
   - All user story acceptance criteria have passing tests
   - TDD methodology documented: Each feature has RED (failing test), GREEN (passing implementation), REFACTOR cycle

3. **Security Validation**:
   - Zero command injection vulnerabilities (shell metacharacter rejection)
   - Zero SSRF vulnerabilities (internal URL blocking)
   - Zero credential leakage (all sensitive data redacted in responses/logs)
   - Multi-tenant isolation verified (no cross-API-key data access)

4. **Performance**:
   - Configuration load time < 100ms
   - Per-request Redis lookup < 10ms
   - No measurable latency increase for requests without server-side MCP

5. **Type Safety**:
   - `ty check` passes with zero errors
   - No `Any` types in new code
   - All functions have explicit type hints

6. **Documentation**:
   - All new public functions have Google-style docstrings
   - CLAUDE.md updated with server-side MCP configuration instructions
   - `.mcp-server-config.json` example provided with comments

## Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Credential Leakage via Config File** | High | Medium | File permission checks, sanitization in all outputs, environment variable resolution server-side only |
| **Cross-Tenant Data Access** | High | Medium | Strict API-key scoping in Redis keys, integration tests for isolation, code review of all database queries |
| **Breaking Backward Compatibility** | High | Low | Comprehensive test suite, merge logic preserves existing per-request behavior, opt-out mechanism |
| **Performance Degradation** | Medium | Low | In-memory config caching, Redis connection pooling, performance benchmarks in CI |
| **Configuration Merge Complexity** | Medium | Medium | Clear precedence rules documented, extensive unit tests for edge cases, merge algorithm code review |
| **Environment Variable Confusion** | Medium | Medium | Documentation clarifying server-side vs client-side resolution, validation warnings |
| **Command Injection in Config** | High | Low | Reuse existing security validators, fuzzing tests with malicious payloads |
| **Redis Unavailability** | Medium | Low | Graceful degradation to application-level config only, retry logic with circuit breaker |
| **TDD Process Compliance** | Low | Medium | Code review checklist enforcing test-first development, CI pipeline verifies test existence before code merge |
| **MCP Server Process Leaks** | Medium | Low | SDK handles lifecycle, monitoring/alerting for zombie processes (out of scope for this phase) |

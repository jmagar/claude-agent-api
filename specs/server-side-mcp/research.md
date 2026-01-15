---
spec: server-side-mcp
phase: research
created: 2026-01-15T16:45:00Z
---

# Research: Server-Side MCP Server Configuration

## Executive Summary

Implementing server-side MCP server configuration is **technically feasible** with **medium complexity**. The feature allows all API requests to automatically access pre-configured MCP servers without requiring per-request configuration. Current architecture already supports per-request MCP configuration, so the primary work involves:

1. Extending `Settings` class for server-side MCP configuration (environment variables or config files)
2. Creating application-level MCP server registry that merges with per-request configs
3. Injecting server-side MCP servers into `QueryRequest` before SDK execution
4. Addressing multi-tenancy concerns (per-API-key MCP server scoping)

**Key Finding**: MCP servers from filesystem discovery (`.claude.json`, `.mcp.json`) are already discovered at the application level but not automatically applied to all requests. The infrastructure exists; it just needs wiring.

## External Research

### Best Practices for Server-Side Tool Configuration

Research into plugin architecture patterns and multi-tenant API systems reveals several key principles:

**Plugin Architecture Patterns** ([Plug-in Architecture - Medium](https://medium.com/omarelgabrys-blog/plug-in-architecture-dec207291800)):
- Core system + plug-in modules for extensibility
- Extension points allow features to be added without core component awareness
- Each plugin can be deployed, tested, and scaled separately

**Server-Side Configuration Management** ([Python Configuration Best Practices](https://coderivers.org/blog/python-config/)):
- Environment variables for simple values (ports, URLs, feature flags)
- JSON/YAML configuration files for structured data (MCP server definitions)
- Pydantic Settings for validation and type safety
- Separate config files per environment (dev, test, prod)

**Multi-Tenant Isolation** ([Multi-Tenancy in REST API - Medium](https://medium.com/@vivekmadurai/multi-tenancy-in-rest-api-a570d728620c), [Azure Multi-Tenant Guide](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/api-management)):
- Tenant identification via JWT claims, API keys, or custom headers
- Per-tenant configuration isolation at API gateway level
- Database-level isolation with Tenant ID columns for shared schemas

**Security Implications**:
- Global tool access requires careful permission boundaries
- MCP servers should be scoped per API key to prevent cross-tenant data leaks
- Sensitive credentials (env vars, headers) must be sanitized in responses

### MCP Server Configuration Patterns

MCP (Model Context Protocol) servers follow standardized configuration formats:

**Configuration Structure** ([MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/)):
```json
{
  "mcpServers": {
    "server-name": {
      "type": "stdio|sse|http",
      "command": "python",
      "args": ["server.py"],
      "env": {"API_KEY": "secret"},
      "headers": {"Authorization": "Bearer token"},
      "url": "https://example.com/mcp"
    }
  }
}
```

**Transport Types** ([MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)):
1. **stdio**: Local process spawned via command + args
2. **sse**: Server-Sent Events over HTTP (long-lived connection)
3. **http**: HTTP-based JSON-RPC communication

**Lifecycle Management** ([MCP Lifecycle Guide](https://medium.com/@ashishpandey2062/mcp-lifecycle-explained-client-server-workflow-c366fd45328b)):
- **Initialization**: Capability negotiation handshake with protocol version agreement
- **Operation**: Message exchange and tool execution during longest phase
- **Shutdown**: Graceful termination with SIGTERM → SIGKILL fallback

**Security Best Practices** ([MCP Best Practices 2026](https://www.cdata.com/blog/mcp-server-best-practices-2026)):
- OAuth 2.1 for HTTP-based transports (replacing basic API keys)
- Least privilege principle: default read-only tools
- Structured YAML configs with environment-specific overrides
- Secrets management via environment variables, never hardcoded

### Configuration Storage Options

**Option 1: Environment Variables**

*Pros*:
- Simple for single MCP server configurations
- Standard 12-factor app pattern
- Easy CI/CD integration

*Cons*:
- Poor for structured data (JSON/nested configs)
- Difficult to maintain multiple MCP servers
- Limited to string values only

*Example*:
```bash
MCP_SERVER_1_NAME="github"
MCP_SERVER_1_COMMAND="npx"
MCP_SERVER_1_ARGS="@modelcontextprotocol/server-github"
MCP_SERVER_2_NAME="postgres"
MCP_SERVER_2_COMMAND="npx"
...
```

**Option 2: JSON Environment Variable** ([Structured Data in Env Vars](https://charemza.name/blog/posts/software-engineering/devops/structured-data-in-environment-variables/))

*Pros*:
- Supports complex nested structures
- Single environment variable for all MCP servers
- Can be parsed by Pydantic

*Cons*:
- Difficult to read/edit in shell
- Escaping challenges in Docker/Kubernetes
- Limited size (OS-dependent, typically 1MB max)

*Example*:
```bash
MCP_SERVERS='{"github":{"type":"stdio","command":"npx","args":["@modelcontextprotocol/server-github"]}}'
```

**Option 3: Configuration File** (RECOMMENDED)

*Pros*:
- Clean separation of configuration from code
- Easy to edit and version control
- Supports comments and validation
- Aligns with existing `.mcp.json` discovery pattern

*Cons*:
- Requires file system access
- Additional deployment artifact

*Example* (`.mcp-server-config.json`):
```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
    },
    "postgres": {
      "type": "stdio",
      "command": "mcp-server-postgres",
      "args": ["--connection", "${DATABASE_URL}"]
    }
  }
}
```

**Option 4: Database Storage**

*Pros*:
- Dynamic configuration changes without restarts
- Per-API-key MCP server scoping
- Audit trail for configuration changes

*Cons*:
- Increased complexity
- Database dependency for configuration
- Performance overhead for every request

*Current Implementation*: Redis-backed storage in `McpServerConfigService` already exists for per-tenant MCP server management.

**Recommendation**: **Hybrid approach** - Configuration file for global defaults + database for per-API-key overrides.

## Codebase Analysis

### Current MCP Integration

**Schema Definition** (`apps/api/schemas/requests/config.py` lines 38-90):
- `McpServerConfigSchema` defines MCP server configuration
- Supports stdio, SSE, and HTTP transports
- Security validation: command injection prevention, SSRF protection
- Environment variables and headers supported

**Per-Request Configuration** (`apps/api/schemas/requests/query.py` line 75):
```python
mcp_servers: dict[str, McpServerConfigSchema] | None = None
```

**SDK Options Building** (`apps/api/services/agent/options.py` lines 99-153):
- `OptionsBuilder._build_mcp_configs()` converts API schema to SDK format
- **CRITICAL SECURITY NOTE (line 143-144)**: Environment variables from user input are NOT resolved to prevent server-side secret leakage
- MCP configs passed directly to `ClaudeAgentOptions(mcp_servers=...)`

**Filesystem Discovery** (`apps/api/services/mcp_discovery.py`):
- Already discovers MCP servers from:
  - Global: `~/.claude.json` (mcpServers section)
  - Project: `.mcp.json` or `.claude/mcp.json`
- `McpDiscoveryService.discover_servers()` returns `dict[str, McpServerInfo]`
- **NOT currently applied to all requests** - only used for management endpoints

**Database Storage** (`apps/api/services/mcp_server_configs.py`):
- Redis-backed MCP server configuration storage
- `McpServerConfigService.list_servers()` retrieves all stored servers
- Used by `/mcp-servers` management endpoints
- **NOT currently applied to all requests**

**Management Endpoints** (`apps/api/routes/mcp_servers.py`):
- `GET /mcp-servers` - Lists filesystem + database servers
- `POST /mcp-servers` - Creates database-stored server
- `GET /mcp-servers/{name}` - Retrieves server by name
- Filesystem servers prefixed with `fs:` to distinguish from database

### Existing Patterns

**Configuration Pattern** (`apps/api/config.py`):
- `Settings` class with Pydantic validation
- Environment variable loading via `pydantic_settings`
- Fields include `api_key`, `database_url`, `redis_url`, etc.
- Example complex field: `cors_origins: list[str]` (line 28)

**Dependency Injection Pattern**:
- Protocol-based abstractions in `apps/api/protocols.py`
- Implementations in `apps/api/adapters/`
- FastAPI `Depends()` for DI injection
- Example: `Cache` protocol → `RedisCache` adapter

**Request Enrichment Pattern**:
- `QueryEnrichmentService` in `apps/api/services/query_enrichment.py`
- Enriches requests with discovered data before execution
- Could be extended for server-side MCP injection

### Dependencies

**Existing Libraries**:
- `pydantic-settings>=2.12.0` - Environment variable configuration
- `redis>=7.1.0` - Cache for MCP server storage
- `structlog>=25.5.0` - Structured logging
- `claude-agent-sdk>=0.1.19` - MCP server support

**No Additional Dependencies Required** - All infrastructure exists.

### Constraints

**Claude Agent SDK Constraints**:
- MCP servers must be passed at options creation time (not dynamically added)
- No SDK API for runtime MCP server registration
- Session resume requires same MCP server configuration

**Security Constraints** (from `apps/api/schemas/requests/config.py`):
- Command injection prevention via `SHELL_METACHAR_PATTERN` validation
- SSRF protection via `validate_url_not_internal()`
- Null byte validation in all string inputs
- **Environment variable resolution disabled** for user input (T140)

**Performance Constraints**:
- MCP server configuration fetched per request
- Redis lookup overhead for database-stored servers
- Filesystem config files read on every discovery (no caching)

## Feasibility Assessment

| Aspect | Assessment | Notes |
|--------|------------|-------|
| **Technical Viability** | High | Infrastructure exists, just needs wiring |
| **Effort Estimate** | M | 3-5 days (config loading + merging + testing) |
| **Risk Level** | Medium | Multi-tenancy isolation critical for security |
| **Complexity** | Medium | Config merging logic + per-API-key scoping |
| **Performance Impact** | Low | One-time config load per request (cacheable) |
| **Security Risk** | Medium | Requires careful tenant isolation design |

**Key Risks**:

1. **Multi-Tenancy Isolation**:
   - Risk: Global MCP servers accessible to all API keys
   - Mitigation: Implement per-API-key MCP server scoping

2. **Configuration Merge Conflicts**:
   - Risk: Per-request config conflicts with server-side config
   - Mitigation: Clear precedence rules (per-request overrides server-side)

3. **Credential Leakage**:
   - Risk: Server-side env vars exposed in responses
   - Mitigation: Sanitize configs before returning (already done in `/mcp-servers` routes)

4. **Performance Degradation**:
   - Risk: Loading config on every request adds latency
   - Mitigation: Cache parsed config in application memory

## Recommended Approach

### Architecture Design

**Three-Tier Configuration System**:

1. **Application-Level (Global)**:
   - Filesystem config: `.mcp-server-config.json` (new file)
   - Loaded at application startup
   - Applies to ALL requests unless overridden

2. **API-Key-Level (Per-Tenant)**:
   - Database-stored configs in Redis (existing `McpServerConfigService`)
   - Associated with specific API keys
   - Overrides application-level configs

3. **Request-Level (Per-Query)**:
   - Existing `QueryRequest.mcp_servers` field
   - Highest priority, overrides both levels above

**Merge Strategy**:
```python
final_mcp_servers = {
    **application_level_servers,  # Lowest priority
    **api_key_level_servers,       # Medium priority
    **request_level_servers,       # Highest priority (existing behavior)
}
```

### Implementation Plan

**Phase 1: Configuration Loading**

1. Extend `Settings` class with optional MCP config file path:
   ```python
   mcp_config_file: str | None = Field(
       default=".mcp-server-config.json",
       description="Path to server-side MCP server config"
   )
   ```

2. Create `McpConfigLoader` service:
   ```python
   class McpConfigLoader:
       def load_application_config(self, path: Path) -> dict[str, McpServerInfo]
       def load_api_key_config(self, api_key: str) -> dict[str, McpServerInfo]
       def merge_configs(
           self,
           application: dict,
           api_key: dict,
           request: dict | None
       ) -> dict[str, McpServerConfigSchema]
   ```

3. Integrate with existing `McpDiscoveryService`:
   - Already discovers filesystem configs
   - Extend to include `.mcp-server-config.json` as additional source

**Phase 2: API-Key Association**

1. Create `ApiKeyMcpMapping` table/cache structure:
   ```python
   # Redis key format: mcp_mapping:{api_key}
   {
       "api_key": "key-12345",
       "mcp_servers": ["github", "postgres"],  # Server names to enable
       "disabled_servers": ["slack"]  # Explicitly disabled
   }
   ```

2. Extend `McpServerConfigService`:
   ```python
   async def get_servers_for_api_key(
       self, api_key: str
   ) -> dict[str, McpServerRecord]
   ```

**Phase 3: Request Enrichment**

1. Create `ServerSideMcpInjector` service:
   ```python
   class ServerSideMcpInjector:
       def __init__(
           self,
           config_loader: McpConfigLoader,
           mcp_config_service: McpServerConfigService
       ):
           ...

       async def inject_server_side_mcp(
           self,
           request: QueryRequest,
           api_key: str
       ) -> QueryRequest:
           # Load application-level config
           app_config = self.config_loader.load_application_config()

           # Load API-key-level config
           api_key_config = await self.mcp_config_service.get_servers_for_api_key(api_key)

           # Merge with request-level config
           merged = self.config_loader.merge_configs(
               app_config,
               api_key_config,
               request.mcp_servers
           )

           # Return enriched request
           return request.model_copy(update={"mcp_servers": merged})
   ```

2. Integrate into `AgentService.query_stream()`:
   ```python
   async def query_stream(
       self, request: QueryRequest, api_key: str
   ) -> AsyncGenerator[dict[str, str], None]:
       # Inject server-side MCP servers BEFORE building options
       enriched_request = await self.mcp_injector.inject_server_side_mcp(
           request, api_key
       )

       # Continue with existing flow
       options = OptionsBuilder(enriched_request).build()
       ...
   ```

**Phase 4: Management Endpoints**

1. Extend `/mcp-servers` routes:
   ```python
   POST /mcp-servers/{name}/assign-to-key
   DELETE /mcp-servers/{name}/revoke-from-key
   GET /mcp-servers/for-key/{api_key}
   ```

2. Add configuration audit logging:
   - Log when server-side MCP servers are injected
   - Include API key, request ID, merged server list

### Configuration File Format

**Recommended Location**: `.mcp-server-config.json` in project root

**Schema**:
```json
{
  "$schema": "./schemas/mcp-server-config.schema.json",
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "type": "stdio",
      "command": "mcp-server-postgres",
      "args": ["--connection", "${DATABASE_URL}"],
      "enabled": true
    },
    "slack": {
      "type": "sse",
      "url": "https://mcp.slack.com/v1",
      "headers": {
        "Authorization": "Bearer ${SLACK_API_TOKEN}"
      },
      "enabled": false
    }
  },
  "apiKeyMappings": {
    "default": ["github", "postgres"],
    "premium-tier": ["github", "postgres", "slack"]
  }
}
```

**Validation Schema** (JSON Schema v7):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "mcpServers": {
      "type": "object",
      "patternProperties": {
        "^[a-zA-Z0-9_-]+$": {
          "type": "object",
          "properties": {
            "type": {"enum": ["stdio", "sse", "http"]},
            "command": {"type": "string"},
            "args": {"type": "array", "items": {"type": "string"}},
            "url": {"type": "string", "format": "uri"},
            "headers": {"type": "object"},
            "env": {"type": "object"},
            "enabled": {"type": "boolean", "default": true}
          },
          "required": ["type"]
        }
      }
    },
    "apiKeyMappings": {
      "type": "object",
      "patternProperties": {
        ".*": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

## Security Considerations

### Risks and Mitigation Strategies

**Risk 1: Credential Leakage**

*Threat*: Server-side MCP configs contain sensitive credentials (API keys, tokens) that could be exposed in API responses.

*Mitigation*:
- Sanitize MCP configs before returning via API (already implemented in `apps/api/routes/mcp_servers.py` lines 62-78)
- Use `***REDACTED***` for sensitive fields in responses
- Never log raw MCP server credentials (use structured logging with sanitization)

**Risk 2: Cross-Tenant Access**

*Threat*: User with API key A accesses MCP servers configured for API key B.

*Mitigation*:
- Implement strict API-key-to-MCP-server mapping in database
- Validate API key ownership before returning MCP configs
- Add audit logging for all MCP server access (who, what, when)

**Risk 3: SSRF via MCP URLs**

*Threat*: Attacker provides internal URL (http://169.254.169.254/metadata) to access cloud metadata or internal services.

*Mitigation*:
- Already implemented: `validate_url_not_internal()` in `apps/api/schemas/validators.py`
- Apply same validation to server-side configs during load
- Reject private IP ranges, localhost, link-local addresses

**Risk 4: Command Injection**

*Threat*: Malicious command in MCP server config executes arbitrary code on server.

*Mitigation*:
- Already implemented: `SHELL_METACHAR_PATTERN` validation in `McpServerConfigSchema`
- Apply same validation to server-side configs during load
- Use allowlist of known-safe commands (e.g., npx, python, node)

**Risk 5: Resource Exhaustion**

*Threat*: Many MCP servers configured per API key, consuming server resources (memory, file descriptors).

*Mitigation*:
- Implement max MCP servers per API key limit (e.g., 10)
- Add rate limiting to `/mcp-servers` management endpoints
- Monitor MCP server process spawning and connection counts

**Risk 6: Configuration Tampering**

*Threat*: Unauthorized modification of server-side MCP config file.

*Mitigation*:
- File permissions: Read-only for application user
- Config file checksum validation at startup
- Alert on config file changes via file integrity monitoring

## OpenAI Compatibility Implications

**Current State**: OpenAI compatibility layer (`/v1/chat/completions`) does NOT expose MCP configuration. Users must use native API endpoint (`/api/v1/query`) to specify MCP servers.

**With Server-Side MCP**:

1. **Automatic Tool Availability**:
   - MCP tools automatically available in OpenAI endpoint responses
   - Tools appear as OpenAI function definitions (future Phase 2 work)
   - No client changes required

2. **Tool Calling Translation** (Future Phase 2):
   - OpenAI `tools` parameter → MCP tool names
   - OpenAI `tool_choice` → MCP tool selection
   - OpenAI `function_call` result → MCP tool result

3. **Transparency**:
   - OpenAI responses include tools from server-side MCP servers
   - Model metadata includes available tool list
   - No client-side MCP configuration needed

**Example OpenAI Request** (with server-side MCP):
```json
POST /v1/chat/completions
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Search GitHub for Python MCP servers"}],
  "tools": [
    {"type": "function", "function": {"name": "github_search", "parameters": {...}}}
  ]
}
```

Server-side MCP `github` server provides `github_search` tool automatically.

## Related Specs Discovery

### Scan of Existing Specs

**Only 1 Other Spec Found**: `openai-api` (completed)

**Relationship Analysis**:

| Spec | Relationship | May Need Update |
|------|--------------|-----------------|
| `openai-api` | **High** - Direct impact | **Yes** |

**Reasoning**:

The `openai-api` spec implemented OpenAI compatibility layer at `/v1/chat/completions`. Currently, this endpoint does NOT expose MCP server configuration (clients must use native `/api/v1/query` endpoint for MCP).

**Impact of Server-Side MCP on OpenAI Compatibility**:

1. **Automatic Tool Availability**: Server-side MCP servers make tools available to OpenAI endpoint automatically, without client configuration.

2. **Future Tool Calling Phase**: When OpenAI tool calling is implemented (Phase 2 of `openai-api` spec), server-side MCP tools will be discoverable via OpenAI's tool format.

3. **Transparency Requirement**: OpenAI endpoint responses should indicate which MCP servers are active (via metadata or logging).

4. **Documentation Update Needed**: `specs/openai-api/decisions.md` should be updated to document server-side MCP integration strategy.

**Recommendation**: Update `openai-api` spec after server-side MCP implementation to document automatic tool availability and plan for Phase 2 tool calling translation.

## Quality Commands

Discovered from `.github/workflows/ci.yml` and `pyproject.toml`:

| Type | Command | Source |
|------|---------|--------|
| Lint | `uv run ruff check .` | `.github/workflows/ci.yml` line 66 |
| Format Check | `uv run ruff format . --check` | `pyproject.toml` (ruff config) |
| Format Fix | `uv run ruff format .` | Ruff auto-fix |
| TypeCheck | `uv run ty check --exit-zero` | `.github/workflows/ci.yml` line 69 |
| Unit Test | `uv run pytest tests/unit` | `.github/workflows/ci.yml` line 72 |
| Contract Test | `uv run pytest tests/contract` | `.github/workflows/ci.yml` line 72 |
| Integration Test | `uv run pytest tests/integration` | Implied from test structure |
| E2E Test | `uv run pytest -m e2e` | `pyproject.toml` marker |
| Test (all) | `uv run pytest` | Default pytest behavior |
| Coverage | `uv run pytest --cov=apps/api --cov-report=term-missing` | `CLAUDE.md` |
| Migrations | `uv run alembic upgrade head` | `.github/workflows/ci.yml` line 63 |

**Local CI Simulation**:
```bash
uv run ruff check . && \
uv run ruff format . --check && \
uv run ty check --exit-zero && \
uv run pytest tests/unit tests/contract --cov=apps/api --cov-report=term-missing
```

**Note**: CI runs tests with PostgreSQL and Redis services. Local development requires Docker Compose services running.

## Open Questions

1. **API Key Tiering**: Should different API key tiers (free, premium) have different MCP server allowances?
   - *Recommendation*: Yes, implement `apiKeyMappings` in config file for tier-based access

2. **Dynamic Config Reload**: Should config file changes apply without server restart?
   - *Recommendation*: No for Phase 1 (requires restart), Yes for Phase 2 (implement file watch + hot reload)

3. **MCP Server Healthchecks**: Should API validate MCP servers are reachable before applying config?
   - *Recommendation*: Optional background health checks with status reporting, but don't block requests

4. **Backwards Compatibility**: Should existing per-request MCP config behavior change?
   - *Recommendation*: No, per-request config maintains highest priority (no breaking changes)

5. **Default Enabled State**: Should all server-side MCP servers be enabled by default, or opt-in?
   - *Recommendation*: Opt-in via `enabled: true` in config file for explicit control

6. **Credential Management**: How should sensitive MCP server credentials be managed?
   - *Recommendation*: Environment variable references (`${VAR_NAME}`) resolved at load time, with validation

## Sources

- [MCP Specification - Model Context Protocol](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Best Practices: Architecture & Implementation Guide](https://modelcontextprotocol.info/docs/best-practices/)
- [MCP Server Best Practices for 2026](https://www.cdata.com/blog/mcp-server-best-practices-2026)
- [MCP Lifecycle Explained: Client–Server Workflow](https://medium.com/@ashishpandey2062/mcp-lifecycle-explained-client-server-workflow-c366fd45328b)
- [Plug-in Architecture - Medium](https://medium.com/omarelgabrys-blog/plug-in-architecture-dec207291800)
- [Multi-Tenancy in REST API - Medium](https://medium.com/@vivekmadurai/multi-tenancy-in-rest-api-a570d728620c)
- [Azure Multi-Tenant API Management](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/api-management)
- [Python Configuration Best Practices](https://coderivers.org/blog/python-config/)
- [Structured Data in Environment Variables](https://charemza.name/blog/posts/software-engineering/devops/structured-data-in-environment-variables/)
- [Best Practices for Python Env Variables](https://dagster.io/blog/python-environment-variables)
- Claude Agent API Codebase (`apps/api/`)

## Appendix: Existing MCP Infrastructure

**Files Involved**:
- `apps/api/config.py` - Settings class (extend for MCP config path)
- `apps/api/schemas/requests/config.py` - `McpServerConfigSchema` (reuse)
- `apps/api/services/mcp_discovery.py` - Filesystem discovery (extend)
- `apps/api/services/mcp_server_configs.py` - Database storage (reuse)
- `apps/api/services/agent/options.py` - SDK options builder (inject merged config)
- `apps/api/routes/mcp_servers.py` - Management endpoints (extend)

**Key Classes**:
- `McpDiscoveryService` - Discovers MCP servers from filesystem
- `McpServerConfigService` - Redis-backed MCP server CRUD
- `OptionsBuilder` - Builds SDK options from request
- `McpServerConfigSchema` - Pydantic schema for MCP server config

**No New Dependencies Required** - All infrastructure exists.

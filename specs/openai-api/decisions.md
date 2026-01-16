# OpenAI API Compatibility - Architectural Decisions

## Document Purpose

This document captures all architectural decisions made during the spec review process for the OpenAI API compatibility layer. Each decision includes rationale, alternatives considered, and implementation guidance.

## SDK Research Findings

### Temperature & Sampling Parameters

**Finding**: The Claude Agent SDK does NOT support temperature, top_p, or stop sequences.

**Evidence**:
- Analyzed `ClaudeAgentOptions` class in `.venv/lib/python3.12/site-packages/claude_agent_sdk/types.py` (lines 616-681)
- No temperature, top_p, or stop parameters in ClaudeAgentOptions
- Searched entire SDK package for temperature/top_p/max_tokens - zero matches
- `extra_args` field exists for "arbitrary CLI flags" but no CLI support for these parameters

**Decision**: **Accept and log warning** for unsupported OpenAI parameters
- Accept temperature, top_p, stop in OpenAI request (validates successfully)
- Log structured warning: `logger.warning("openai.unsupported_parameter", parameter="temperature", value=1.0)`
- Do NOT return error to client (maintain compatibility)
- Document in API docs which parameters are ignored

**Alternatives Considered**:
1. ❌ Reject requests with unsupported parameters - breaks compatibility
2. ❌ Silently ignore - poor observability
3. ✅ Accept and log warning - balances compatibility with observability

### Max Tokens vs Max Turns

**Finding**: SDK uses `max_turns` (conversation turn limit), NOT `max_tokens` (output token limit).

**Evidence**:
- `ClaudeAgentOptions.max_turns: int | None` - limits number of conversation turns
- No `max_tokens` parameter exists in SDK
- OpenAI's `max_tokens=0` means "use default limit"

**Decision**: **Ignore max_tokens parameter completely**
- Do NOT map max_tokens to max_turns (incompatible semantics)
- If client sends max_tokens, log warning and ignore
- Let SDK use its default turn limit
- Document in API that max_tokens is unsupported

**Alternatives Considered**:
1. ❌ Map max_tokens to max_turns with heuristic (500 tokens = 1 turn) - inaccurate and misleading
2. ❌ Set max_turns=1 for max_tokens=0 - breaks conversation flow
3. ✅ Ignore completely - honest about limitations

### Message History & Session Management

**Finding**: SDK maintains conversation state internally via session IDs, NOT via message history arrays.

**Evidence**:
- `ClaudeAgentOptions.resume: str | None` - resume existing session by ID
- `ClaudeAgentOptions.continue_conversation: bool` - continue without explicit resume
- `ClaudeAgentOptions.fork_session: bool` - fork existing session
- No message history parameter in SDK

**OpenAI API Behavior**:
- Client sends FULL message history in every request: `[{role: "user", content: "..."}, {role: "assistant", content: "..."}, ...]`
- Server is stateless - all conversation context comes from message array
- Conversation continuity achieved by client maintaining and sending history

**Our Implementation Strategy**:

For **new conversations** (no session_id):
1. Concatenate ALL messages from OpenAI message array into single prompt string
2. Use role prefixes for multi-turn simulation:
   ```
   SYSTEM: You are a helpful assistant

   USER: Hello

   ASSISTANT: Hi there!

   USER: What's the weather?
   ```
3. Pass concatenated prompt to SDK query()
4. SDK creates new session and returns session_id

For **resumed conversations** (existing session_id):
1. Look up session_id from previous conversation (map OpenAI conversation → SDK session)
2. Extract ONLY the last user message from OpenAI message array
3. Pass last message + session_id to SDK with `resume=session_id`
4. SDK appends to existing conversation state

**Session Mapping**:
- Maintain Redis cache: `openai_conversation_hash → sdk_session_id`
- Hash = SHA256(first 3 messages) to identify conversation
- Allows stateless OpenAI API to map to stateful SDK sessions

**Decision**: **Concatenate messages for new sessions, resume for existing sessions**

**Alternatives Considered**:
1. ❌ Always concatenate all messages - ignores SDK session management
2. ❌ Only use last message always - loses conversation context
3. ✅ Smart routing based on session state - leverages SDK strengths

## Type Safety Decisions

### Type Checker Selection

**Decision**: **Use `ty` as primary type checker, remove mypy**

**Rationale**:
- ty is Astral's new fast type checker (aligns with uv, ruff ecosystem)
- Zero tolerance for `Any` types - ty catches these strictly
- Faster than mypy for large codebases
- Project already uses uv and ruff (Astral stack)

**Implementation**:
- Update tasks.md: Replace all `uv run mypy` with `uv run ty check`
- Update design.md: Change type checking section to reference ty
- Keep mypy config temporarily for backwards compatibility
- Add `uv run ty check` to quality checkpoints

### Type Strategy for JSON Structures

**Decision**: **Pydantic for requests, TypedDict for responses**

**Rationale**:
- Pydantic: Runtime validation, coercion, error messages (ideal for untrusted input)
- TypedDict: Zero runtime overhead, pure type hints (ideal for internal/output data)
- Existing codebase uses this pattern (`apps/api/schemas/requests.py` vs `apps/api/schemas/responses.py`)

**Implementation**:
- OpenAI request schemas: Pydantic models in `apps/api/schemas/openai/requests.py`
- OpenAI response schemas: TypedDict in `apps/api/types.py` (extend existing file)
- Translation layer internal types: TypedDict (no validation needed)

**Alternatives Considered**:
1. ❌ Pydantic everywhere - unnecessary runtime overhead for responses
2. ❌ TypedDict everywhere - lose request validation
3. ✅ Hybrid approach - best of both worlds

### TypedDict Location

**Decision**: **Extend existing `apps/api/types.py` file**

**Rationale**:
- File already exists with native API TypedDict definitions
- Keep all TypedDict definitions in one place (Single Responsibility)
- Avoids creating new `apps/api/schemas/openai/types.py` (redundant)

**Implementation**:
- Add OpenAI TypedDict definitions to `apps/api/types.py`
- Group with comment header: `# OpenAI API TypedDicts`
- Follow existing pattern in file

## Authentication Decisions

### Auth Strategy

**Decision**: **BearerAuthMiddleware extracts Bearer token, sets X-API-Key header**

**Rationale**:
- OpenAI clients send: `Authorization: Bearer <token>`
- Existing API expects: `X-API-Key: <token>`
- Middleware can bridge the gap without touching existing auth logic

**Implementation**:
1. Create `apps/api/middleware/bearer_auth.py`
2. Middleware checks if route path starts with `/v1`
3. If yes, extract token from `Authorization: Bearer <token>`
4. Set `X-API-Key: <token>` header
5. Existing `ApiKeyAuthMiddleware` validates as normal

**Middleware Order** (critical - FastAPI executes in REVERSE registration order):
```python
# In apps/api/main.py - register in THIS order:
app.add_middleware(ApiKeyAuthMiddleware)     # Executes SECOND (validates X-API-Key)
app.add_middleware(BearerAuthMiddleware)     # Executes FIRST (extracts Bearer → X-API-Key)
```

**Alternatives Considered**:
1. ❌ Create new auth validator for /v1 routes - duplicates logic
2. ❌ Modify existing ApiKeyAuthMiddleware - pollutes existing code
3. ✅ Bridge middleware - zero impact on existing auth

## Error Handling Decisions

### Error Format Translation

**Decision**: **Read `apps/api/exceptions.py` and create exact HTTP status → OpenAI error type mapping**

**Mapping** (based on `apps/api/exceptions.py`):
```python
# HTTP Status → OpenAI Error Type
401 → "invalid_authentication_error"    # Unauthorized
403 → "permission_denied_error"         # Forbidden
400 → "invalid_request_error"           # BadRequest, ValidationError
404 → "invalid_request_error"           # NotFound (treat as bad request)
429 → "rate_limit_exceeded"             # RateLimitExceeded
500 → "api_error"                       # InternalServerError
503 → "overloaded_error"                # ServiceUnavailable
```

**Implementation**:
- Create `apps/api/services/openai/error_translator.py`
- Function: `translate_error(exc: Exception) → OpenAIErrorResponse`
- Reads exception type, maps to OpenAI error format:
  ```typescript
  {
    "error": {
      "type": "invalid_request_error",
      "message": "Missing required field: messages",
      "code": "missing_required_field"
    }
  }
  ```

**Exception Handler Strategy**:
- Add exception handlers in `apps/api/routes/openai/completions.py`
- Check if route path starts with `/v1` - if yes, use OpenAI error format
- If no, use existing error format (zero impact on native API)

**Alternatives Considered**:
1. ❌ Global exception handler - affects all routes
2. ❌ Custom error responses in each endpoint - duplicates logic
3. ✅ Route-specific exception handlers - isolated, clean

## Model Configuration Decisions

### Model Name Mapping

**Decision**: **Dict in Settings class with configurable mappings**

**Rationale**:
- Hardcoded mappings fragile (what if user wants different mapping?)
- Settings class already exists (`apps/api/config.py`)
- Allows customization via environment variables

**Implementation**:
```python
# In apps/api/config.py
class Settings(BaseSettings):
    # ... existing fields ...

    openai_enabled: bool = True
    openai_model_mapping: dict[str, str] = {
        "gpt-4": "sonnet",
        "gpt-4-turbo": "sonnet",
        "gpt-3.5-turbo": "haiku",
        "gpt-4o": "opus",
    }

    @validator("openai_model_mapping", pre=True)
    def parse_model_mapping(cls, v):
        """Parse model mapping from env var JSON string."""
        if isinstance(v, str):
            return json.loads(v)
        return v
```

**Environment Variable**:
```bash
OPENAI_MODEL_MAPPING='{"gpt-4":"sonnet","custom-model":"haiku"}'
```

**Alternatives Considered**:
1. ❌ Hardcoded dict in ModelMapper - not configurable
2. ❌ Database table - overkill for simple mapping
3. ✅ Settings class - standard pattern, env var support

## Server-Side MCP Integration

**Finding**: The API now supports automatic server-side MCP server configuration injection (see `specs/server-side-mcp/spec.md`).

**Evidence**:
- Three-tier configuration system: Application (file) < API-Key (database) < Request
- `McpConfigInjector` service runs before SDK execution in `AgentService`
- All query methods (including OpenAI endpoints) automatically get MCP servers injected

**OpenAI Compatibility Impact**:

### Automatic Tool Availability

OpenAI endpoints (`/v1/chat/completions`) **automatically have access** to server-side MCP servers without client configuration:

```bash
# MCP tools from .mcp-server-config.json are automatically available
curl -X POST http://localhost:54000/v1/chat/completions \
  -H "Authorization: Bearer api-key-123" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Use GitHub MCP tool to create issue"}]
  }'
```

**How It Works**:
1. OpenAI request arrives at `/v1/chat/completions`
2. `BearerAuthMiddleware` extracts API key from Bearer token
3. Request translated to `QueryRequest` via `RequestTranslator`
4. `AgentService.query_stream()` calls `McpConfigInjector.inject()` BEFORE SDK execution
5. Injector merges:
   - Application-level MCP servers (`.mcp-server-config.json`)
   - API-key-level MCP servers (Redis database)
   - Request-level MCP servers (if provided in translated request)
6. Enriched `QueryRequest` passed to SDK with merged MCP servers
7. SDK has access to all configured tools for the request

**Decision**: **No changes needed to OpenAI translation layer**

**Rationale**:
- MCP injection happens BEFORE translation layer (in `AgentService`)
- `QueryRequest` already has `mcp_servers` field that injector populates
- OpenAI endpoints inherit MCP support automatically through shared `AgentService`
- Zero code changes required in OpenAI routes/services

**Configuration Precedence**:

OpenAI clients can override server-side MCP configs by providing explicit server configuration:

```python
# Via native API with explicit MCP servers
request = QueryRequest(
    prompt="...",
    mcp_servers={
        "custom-tool": {
            "type": "stdio",
            "command": "custom-mcp-server"
        }
    }
)
```

Note: OpenAI `/v1/chat/completions` endpoint does NOT support MCP server configuration in request body (OpenAI API spec limitation). To use custom MCP servers:
1. Configure in `.mcp-server-config.json` (application-level)
2. Add via `/api/v1/mcp-servers` endpoint (API-key-level)
3. Use native `/api/v1/query` endpoint (request-level override supported)

**Phase 2 Tool Calling**:

When Phase 2 implements OpenAI tool calling format, server-side MCP integration provides the foundation:

1. **Tool Discovery**: List available tools from merged MCP servers
2. **Tool Execution**: Execute MCP tool when OpenAI client requests tool_call
3. **Result Translation**: Map MCP tool results back to OpenAI tool_call response format

**Implementation Notes**:
- MCP servers configured at application/API-key level appear as "available tools" in OpenAI tool calling
- Tool execution delegated to SDK (which already supports MCP)
- Translation layer only needs to map tool metadata (name, parameters, description)

**Security**:
- All server-side MCP configurations validated for:
  - Command injection (shell metacharacters blocked)
  - SSRF prevention (internal URLs blocked)
  - Credential sanitization (secrets redacted in logs)
- Multi-tenant isolation via API-key scoping (no cross-tenant access)

**Testing**:
- Contract test verifies OpenAI endpoint receives server-side MCP configs: `test_openai_endpoint_includes_server_side_mcp`
- Integration tests verify three-tier merge works end-to-end
- Security tests verify validation rules enforced

For detailed server-side MCP documentation, see:
- [Server-Side MCP Spec](../server-side-mcp/spec.md)
- [Server-Side MCP Requirements](../server-side-mcp/requirements.md)
- [Server-Side MCP Design](../server-side-mcp/design.md)
- [CLAUDE.md - Server-Side MCP Configuration](../../CLAUDE.md#server-side-mcp-configuration)

## SSE Streaming Decisions

### Native SSE Event Format

**Finding**: Native API SSE events are structured Pydantic models, NOT plain dicts.

**Evidence**:
- Analyzed `apps/api/schemas/responses.py` (lines 305-359)
- Native events: `InitEvent`, `MessageEvent`, `PartialMessageEvent`, `ResultEvent`, `ErrorEvent`, `DoneEvent`
- Each event has `event: Literal["init"|"message"|...]` and `data: <EventDataSchema>`
- Events serialized as: `event: message\ndata: {"type":"assistant",...}\n\n`

**OpenAI SSE Format**:
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"},"index":0}]}

data: [DONE]
```

**Decision**: **Parse native events, map to OpenAI chunks**

**Implementation**:
1. Subscribe to native SSE stream from query endpoint
2. Parse each event (already Pydantic models, not raw JSON)
3. StreamingAdapter maps native event → OpenAI chunk:
   - `MessageEvent` with text content → `delta: {content: "text"}`
   - `PartialMessageEvent` (content_block_delta) → `delta: {content: "text"}`
   - `ResultEvent` → final chunk with `finish_reason`
   - `DoneEvent` → `data: [DONE]`
4. Maintain completion_id state across chunks (UUID generated at stream start)

**Alternatives Considered**:
1. ❌ Raw string parsing of SSE - fragile, ignores types
2. ❌ Re-serialize to JSON then parse - unnecessary overhead
3. ✅ Use structured Pydantic models - type-safe, efficient

### No Text Content Handling

**Decision**: **Serialize tool_use blocks as text for OpenAI compatibility**

**Rationale**:
- Native API can return only tool_use blocks (no text content)
- OpenAI format expects `content` field with text
- Need to provide something meaningful for clients

**Implementation**:
```python
def extract_text_content(blocks: list[ContentBlock]) -> str:
    """Extract text from content blocks, serialize tool_use if no text."""
    texts = [b.text for b in blocks if isinstance(b, TextBlock)]

    if texts:
        return "\n\n".join(texts)

    # No text blocks - serialize tool_use for visibility
    tool_uses = [b for b in blocks if isinstance(b, ToolUseBlock)]
    if tool_uses:
        return "\n".join(
            f"[Tool: {t.name}]\nInput: {json.dumps(t.input, indent=2)}"
            for t in tool_uses
        )

    return ""  # Empty response (shouldn't happen but handle gracefully)
```

**Alternatives Considered**:
1. ❌ Return empty string - loses information
2. ❌ Return error - breaks valid responses
3. ✅ Serialize tool_use as text - maintains visibility

## Stop Reason Mapping

**Decision**: **Map SDK stop reasons to OpenAI finish reasons with fallback**

**Mapping**:
```python
# SDK stop_reason → OpenAI finish_reason
"completed" → "stop"
"max_turns_reached" → "length"
"interrupted" → "stop"
"error" → "stop"
None → "stop"  # Default fallback
```

**Unknown Stop Reason Handling**:
- If SDK returns unknown stop_reason (future-proofing):
  1. Log warning: `logger.warning("openai.unknown_stop_reason", reason=unknown_value)`
  2. Default to `"stop"` (safest assumption)
  3. Do NOT raise error (graceful degradation)

**Implementation**:
```python
STOP_REASON_MAP = {
    "completed": "stop",
    "max_turns_reached": "length",
    "interrupted": "stop",
    "error": "stop",
}

def map_stop_reason(sdk_reason: str | None) -> str:
    """Map SDK stop reason to OpenAI finish reason."""
    if sdk_reason is None:
        return "stop"

    if sdk_reason in STOP_REASON_MAP:
        return STOP_REASON_MAP[sdk_reason]

    # Unknown reason - log and default to 'stop'
    logger.warning("openai.unknown_stop_reason", reason=sdk_reason)
    return "stop"
```

## Protocol Definitions

**Decision**: **Create `apps/api/protocols/openai.py` for translation layer abstractions**

**Rationale**:
- Existing codebase uses Protocol-based dependency injection
- Protocols in `apps/api/protocols.py` - add new file for OpenAI-specific protocols
- Clean separation from existing protocols

**Implementation**:
```python
# apps/api/protocols/openai.py
from typing import Protocol

class RequestTranslatorProtocol(Protocol):
    """Translates OpenAI requests to SDK format."""
    def translate(self, openai_request: ChatCompletionRequest) -> QueryRequest: ...

class ResponseTranslatorProtocol(Protocol):
    """Translates SDK responses to OpenAI format."""
    def translate(self, sdk_response: SingleQueryResponse) -> ChatCompletion: ...

class StreamingAdapterProtocol(Protocol):
    """Adapts SDK SSE stream to OpenAI streaming format."""
    async def adapt(self, native_stream: AsyncIterator[Event]) -> AsyncIterator[str]: ...

class ModelMapperProtocol(Protocol):
    """Maps OpenAI model names to Claude models."""
    def map_model(self, openai_model: str) -> str: ...

class ErrorTranslatorProtocol(Protocol):
    """Translates exceptions to OpenAI error format."""
    def translate(self, exc: Exception) -> OpenAIErrorResponse: ...
```

## Performance & Quality Decisions

### Benchmarking

**Decision**: **Defer benchmarks to Phase 3**

**Rationale**:
- Phase 1 (MVP) focuses on correctness and functionality
- Premature optimization wastes time
- Need working implementation before meaningful benchmarks

**Phase 3 Benchmarks** (deferred):
- Request translation latency (<5ms target)
- Response translation latency (<10ms target)
- First streaming chunk time (<50ms target)
- End-to-end request/response time
- Memory usage under load

### Test Coverage

**Decision**: **≥90% coverage for services (unit), ≥80% for routes (integration)**

**Rationale**:
- Services are pure logic - should be highly tested
- Routes involve I/O and integration - harder to test every path
- 100% coverage not pragmatic (diminishing returns)

**Implementation**:
- pytest with pytest-cov
- Quality checkpoint after each phase verifies coverage
- Block PR merge if coverage drops below threshold

## Implementation Phase Strategy

**Decision**: **Fix all critical issues in specs NOW before implementation**

**Rationale**:
- 26 critical issues identified across research.md, requirements.md, design.md, tasks.md
- Implementing with flawed specs leads to rework
- Better to invest 1-2 hours fixing specs than 5+ hours fixing code

**Critical Issues to Fix**:
1. Update research.md: Add ty, clarify auth, document session management
2. Update requirements.md: Remove `Any` types, add acceptance criteria, map parameters correctly
3. Update design.md: Add Protocol definitions, correct SSE event types, fix Pydantic vs TypedDict
4. Update tasks.md: Correct QueryRequest field names, fix native event assumptions, add SDK research tasks

**Next Steps**:
1. ✅ Complete SDK research (done)
2. ✅ Document decisions (this file)
3. 🔄 Fix critical issues in specs (next)
4. 🔄 Update tasks.md with research findings
5. 🔄 Begin implementation (after specs validated)

## Summary

### Key Takeaways

1. **SDK Limitations**: Temperature, top_p, max_tokens, stop sequences NOT supported - accept and log warnings
2. **Message History**: Concatenate for new sessions, resume existing sessions via session_id mapping
3. **Type Safety**: ty (primary), Pydantic (requests), TypedDict (responses), zero `Any` types
4. **Authentication**: BearerAuthMiddleware extracts Bearer token → X-API-Key header
5. **SSE Streaming**: Parse native Pydantic events, map to OpenAI chunks with stateful completion_id
6. **Error Handling**: Route-specific exception handlers, HTTP status → OpenAI error type mapping
7. **Model Config**: Dict in Settings with env var support for customization
8. **Server-Side MCP**: OpenAI endpoints automatically get MCP tools from application/API-key configs - zero translation layer changes needed
9. **Quality**: Fix specs before coding, ≥90% service coverage, ≥80% route coverage

### Tradeoffs Accepted

1. **No temperature/top_p support**: Accept limitation, log warnings (SDK constraint)
2. **max_tokens ignored**: Don't map to max_turns (incompatible semantics)
3. **Session mapping overhead**: Redis cache adds latency but enables stateless OpenAI API
4. **Tool_use serialization**: Serialize as text when no text content (visibility over purity)
5. **Unknown stop reasons**: Default to "stop" (graceful degradation over errors)

### Next Actions

1. Fix critical issues in research.md, requirements.md, design.md, tasks.md
2. Add pre-implementation SDK research tasks (1.0.1-1.0.3) to tasks.md
3. Update tasks.md with actual QueryRequest fields and SDK constraints
4. Begin Phase 1 implementation following strict TDD (RED-GREEN-REFACTOR)

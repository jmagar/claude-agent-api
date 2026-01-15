---
spec: openai-api
phase: research
created: 2026-01-14T15:30:00Z
---

# Research: OpenAI API Compatibility

## Executive Summary

Adding OpenAI API compatibility to the Claude Agent API requires implementing a translation layer that maps OpenAI's `/v1/chat/completions` endpoint to our existing `/api/v1/query` endpoint. The core challenge is adapting OpenAI's message-based chat format to Claude Agent SDK's prompt-based query model while maintaining streaming SSE compatibility. This is highly feasible with medium complexity, requiring new endpoint routes, request/response translation logic, and careful handling of streaming vs non-streaming modes.

## External Research

### OpenAI API Standard

The OpenAI Chat Completions API has become the de facto standard for LLM inference APIs. Key characteristics:

**Endpoint Structure:**
- `POST /v1/chat/completions` - Primary chat endpoint
- `POST /v1/completions` - Legacy text completions (deprecated)
- `POST /v1/embeddings` - Text embeddings (out of scope)
- `GET /v1/models` - List available models

**Request Schema:**
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's the weather?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false,
  "tools": [...],
  "tool_choice": "auto"
}
```

**Response Schema (Non-Streaming):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

**Streaming Response (SSE):**
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"gpt-4","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**Key Parameters:**
- `model` (required): Model identifier (e.g., "gpt-4", "gpt-3.5-turbo")
- `messages` (required): Array of conversation messages with roles
- `temperature` (optional, 0-2): Sampling temperature
- `max_tokens` (optional): Maximum tokens to generate
- `stream` (optional, boolean): Enable SSE streaming
- `tools` (optional): Function/tool definitions for tool calling
- `tool_choice` (optional): Control tool selection ("auto", "none", specific tool)
- `top_p` (optional, 0-1): Nucleus sampling parameter
- `presence_penalty` (optional, -2 to 2): Penalize new tokens based on presence
- `frequency_penalty` (optional, -2 to 2): Penalize repeated tokens
- `stop` (optional): Stop sequences
- `user` (optional): End-user identifier for tracking
- `logit_bias` (optional): Token bias mapping
- `logprobs` (optional): Return log probabilities
- `n` (optional): Number of completions to generate
- `seed` (optional): Deterministic sampling seed

**2026 Updates:**
- `reasoning_effort`: Controls reasoning depth (none, minimal, low, medium, high, xhigh)
- `verbosity`: Response conciseness (low, medium, high)
- `prompt_cache_key`: Cache optimization for similar requests
- `prompt_cache`: Retention policy ("24h" for extended caching)
- `store`: Enable storage for later modification

### Best Practices from Industry

**From vLLM Implementation:**
- Use `extra_body` field for provider-specific parameters
- Support both string and structured content formats
- Maintain OpenAI error codes and status codes
- Implement `/v1` prefix for all endpoints
- Support `X-Request-Id` header for request tracking
- Use chat templates (Jinja2) for message formatting
- Handle tool calling with `parallel_tool_calls` parameter

**From LiteLLM/LMStudio:**
- Accept OpenAI Python client with only `base_url` change
- Require API key even if using dummy values
- Map unsupported parameters gracefully (ignore or approximate)
- Use model name prefixes for routing (`openai/model-name`)
- Support `v1/models` endpoint for client compatibility
- Return proper OpenAI-format errors with `error` object

**Common Implementation Patterns:**
1. **Dual Endpoint Strategy**: Maintain both native and OpenAI-compatible endpoints
2. **Request Translation**: Convert OpenAI format → native format at API boundary
3. **Response Wrapping**: Native response → OpenAI format before returning
4. **Streaming Adapter**: Translate native SSE events to OpenAI chunk format
5. **Model Mapping**: Map OpenAI model names to internal model identifiers
6. **Parameter Subset**: Implement core parameters, ignore/log unsupported ones

### Pitfalls to Avoid

**From Research:**
- Don't add `/v1` to `base_url` in configuration - client adds it automatically
- Don't fail on unknown parameters - log warnings and continue
- Don't implement all parameters initially - focus on essential ones
- Don't break native API when adding compatibility layer
- Handle system message incompatibility (some models don't support it)
- Avoid silent parameter drops - log when ignoring unsupported parameters
- Don't assume message history format matches SDK expectations
- Be careful with streaming: OpenAI uses `delta` field, not full content

## Codebase Analysis

### Existing Architecture

**Current Query Endpoint (`/api/v1/query`):**
- Uses `QueryRequest` schema with single `prompt` string
- Returns custom SSE events: `init`, `message`, `question`, `partial`, `result`, `error`, `done`
- Streaming via `sse-starlette.EventSourceResponse`
- Non-streaming via `/query/single` endpoint
- Session management built into query flow
- Tool configuration via `allowed_tools`/`disallowed_tools` arrays

**Request Schema (`QueryRequest`):**
```python
class QueryRequest(BaseModel):
    prompt: str                    # Single prompt, not message array
    images: list[ImageContentSchema] | None
    session_id: str | None        # For resuming conversations
    fork_session: bool
    continue_conversation: bool
    allowed_tools: list[str]      # Tool allow/deny lists
    disallowed_tools: list[str]
    permission_mode: Literal[...]
    model: str | None             # "sonnet", "opus", "haiku"
    max_turns: int | None         # Different from max_tokens
    # ... many more fields
```

**Response Schema (`SingleQueryResponse`):**
```python
class SingleQueryResponse(BaseModel):
    session_id: str
    model: str
    content: list[ContentBlockSchema]  # Structured content blocks
    is_error: bool
    stop_reason: Literal[...]
    duration_ms: int
    num_turns: int                     # Turn count, not token count
    total_cost_usd: float | None
    usage: UsageSchema | None          # Token usage data
```

**SSE Events:**
```python
# Current event types (apps/api/schemas/responses.py)
# IMPORTANT: These are Pydantic models (BaseModel subclasses), NOT plain dicts
InitEvent: session_id, model, tools, mcp_servers, plugins
MessageEvent: type (user|assistant|system), content blocks, usage
QuestionEvent: AskUserQuestion tool use
PartialMessageEvent: Streaming content deltas (content_block_start, content_block_delta, content_block_stop)
ResultEvent: Final result with stats, stop_reason enum: "completed"|"max_turns_reached"|"interrupted"|"error"
ErrorEvent: Error information
DoneEvent: Stream completion marker

# Event format: `event: <type>\ndata: <json>\n\n`
# Example: event: message\ndata: {"event":"message","data":{"type":"assistant",...}}\n\n
```

**Streaming Flow:**
1. Client POSTs to `/api/v1/query`
2. `query_stream()` enriches query with MCP servers
3. `agent_service.query_stream()` yields SSE events
4. Events: init → message* → partial* → result → done
5. Session created/updated in PostgreSQL + Redis

**Non-Streaming Flow:**
1. Client POSTs to `/api/v1/query/single`
2. `query_single()` enriches query
3. `agent_service.query_single()` returns complete result
4. Response mapped to `SingleQueryResponse` schema

### Existing Patterns

**Protocol-Based Dependency Injection:**
```python
# apps/api/protocols.py defines abstractions
# apps/api/adapters/ implements concrete adapters
# FastAPI dependencies inject via Depends()
```

**Request Validation:**
- Pydantic models with field validators
- Security checks: path traversal, null bytes, environment variable injection
- Tool name validation against built-in tools list

**Error Handling:**
- Custom exception hierarchy (`apps/api/exceptions/`)
- Exception handlers in `main.py` convert to JSON responses
- Structured error format with `code`, `message`, `details`

**Message Mapping:**
```python
# apps/api/schemas/messages.py
def map_sdk_content_block(block: dict) -> dict:
    # Maps SDK content blocks to API schema
    # Handles: text, thinking, tool_use, tool_result
```

### Dependencies

**Existing (Relevant):**
- `fastapi>=0.128.0` - Web framework
- `pydantic>=2.12.5` - Schema validation
- `sse-starlette>=3.1.2` - SSE streaming
- `structlog>=25.5.0` - Structured logging
- `claude-agent-sdk>=0.1.19` - Claude Agent SDK

**No OpenAI Client Needed:**
- We're implementing the **server side**, not calling OpenAI
- Clients will use `openai` Python package or equivalent
- No additional dependencies required for basic compatibility

### Constraints

**Technical Limitations:**
1. **Message History Format**: Current API uses single `prompt` string, not message array
2. **Session Management**: Session ID is internal, OpenAI uses conversation ID differently
3. **Model Names**: Use "sonnet"/"opus"/"haiku", not "gpt-4"/"gpt-3.5-turbo"
4. **Token Limits**: SDK uses `max_turns`, OpenAI uses `max_tokens`
5. **Tool Format**: Different tool definition schemas
6. **Streaming Format**: Different SSE event structures
7. **Stop Reasons**: Different stop reason enum values

**Architectural Constraints:**
1. Must maintain backward compatibility with existing `/api/v1/query` endpoint
2. Cannot modify Claude Agent SDK behavior
3. Must preserve distributed session tracking (PostgreSQL + Redis)
4. Rate limiting configured per-endpoint (needs new config for OpenAI endpoints)
5. Authentication via `X-API-Key` header (OpenAI uses `Authorization: Bearer`)

**SDK Constraints:**
1. Claude Agent SDK doesn't expose conversation history as message array
2. SDK manages its own session state internally via `resume`, `continue_conversation`, `fork_session` options
3. Cannot directly map OpenAI tools to SDK tool format
4. SDK returns structured content blocks, not plain text
5. **Temperature, top_p, max_tokens, stop sequences NOT supported** - SDK has NO sampling control parameters
6. SDK uses `max_turns` (conversation turn limit), NOT `max_tokens` (output token limit)

## Feasibility Assessment

| Aspect | Assessment | Notes |
|--------|------------|-------|
| Technical Viability | **High** | Well-defined mapping between formats, proven patterns from vLLM/LiteLLM |
| Effort Estimate | **M (Medium)** | 3-5 days for core implementation: new routes + translation layer + tests |
| Risk Level | **Low-Medium** | Main risks: message history mapping, streaming translation, tool format conversion |
| Compatibility Coverage | **70-80%** | Can support core parameters, some advanced features may require approximation |
| Breaking Changes | **None** | Additive feature, existing API unchanged |
| Maintenance Burden | **Low-Medium** | Translation layer is isolated, minimal ongoing maintenance |

**Technical Viability: High**
- FastAPI supports multiple route prefixes (add `/v1` alongside `/api/v1`)
- Pydantic can define OpenAI-compatible schemas
- SSE streaming already implemented, just need format translation
- Message array → prompt string conversion is straightforward (join with newlines)
- Model name mapping is simple dictionary lookup

**Key Challenges:**
1. **Message History**: OpenAI clients send full conversation history in every request (stateless server), Claude SDK manages state internally via session_id (stateful)
   - Solution: For NEW conversations - concatenate ALL messages from OpenAI array with role prefixes into single prompt
   - Solution: For RESUMED conversations - map OpenAI conversation hash → SDK session_id (Redis cache), send ONLY last message with `resume=session_id`
   - Trade-off: Adds Redis overhead but enables OpenAI's stateless API to work with SDK's stateful sessions
2. **Streaming Format**: Different SSE event structures
   - Solution: Transform events in middleware/wrapper
3. **Tool Definitions**: Different schemas
   - Solution: Translation layer for tool format (if tools needed initially)
4. **Token vs Turn Limits**: OpenAI uses max_tokens, SDK uses max_turns
   - Solution: Ignore max_tokens completely (incompatible semantics - token output limit vs conversation turns)

**Recommended Approach:**
- **Phase 1** (MVP): `/v1/chat/completions` for basic text generation (no tools)
  - Core parameters: model, messages, stream (NOTE: temperature, top_p, max_tokens, stop NOT supported by SDK)
  - Accept unsupported parameters and log warnings for observability
  - Map to existing QueryRequest internally
  - Transform responses to OpenAI format
- **Phase 2** (Tools): Add tool calling support
  - Translate OpenAI tool definitions to SDK format
  - Map tool_use/tool_result content blocks
- **Phase 3** (Advanced): Additional parameters
  - top_p, presence_penalty, frequency_penalty
  - Multi-turn conversation optimization
  - `/v1/models` endpoint

## Recommendations for Requirements

### Core Requirements

1. **Implement `/v1/chat/completions` Endpoint**
   - Accept OpenAI-compatible request format
   - Support both streaming (`stream: true`) and non-streaming modes
   - Return OpenAI-compatible response format
   - Map model names (gpt-4 → sonnet, gpt-3.5-turbo → haiku)

2. **Request Translation Layer**
   - Convert `messages` array to single `prompt` string
   - Extract system message as `system_prompt` if present
   - Map OpenAI parameters to QueryRequest fields
   - Handle unsupported parameters gracefully (log warning, continue)

3. **Response Translation Layer**
   - Convert `SingleQueryResponse` to OpenAI non-streaming format
   - Transform SSE events to OpenAI streaming chunks
   - Map content blocks to OpenAI message format
   - Generate OpenAI-compatible request IDs

4. **Authentication Compatibility**
   - Accept `Authorization: Bearer <token>` header
   - Map to internal `X-API-Key` authentication
   - Maintain backward compatibility with existing auth

5. **Error Format Mapping**
   - Convert internal APIError to OpenAI error format
   - Maintain proper HTTP status codes
   - Include OpenAI-style error objects

### Optional Enhancements

1. **Implement `/v1/models` Endpoint**
   - Return list of available models
   - Map internal model names to OpenAI-style names
   - Include model capabilities metadata

2. **Tool Calling Support**
   - Translate OpenAI tool definitions to SDK format
   - Map tool_use content blocks to OpenAI format
   - Support `tool_choice` parameter

3. **Advanced Parameters**
   - `top_p`, `presence_penalty`, `frequency_penalty` if SDK supports
   - `stop` sequences
   - `logprobs` (may not be supported by SDK)

4. **Parameter Handling**
   - Accept temperature, top_p, max_tokens, stop for compatibility but log warnings (SDK doesn't support)
   - Ignore max_tokens completely (incompatible with max_turns - different semantics)
   - Log all unsupported parameters with structured logging for observability

### Architecture Recommendations

**Project Structure:**
```
apps/api/
├── routes/
│   ├── openai/           # New directory
│   │   ├── __init__.py
│   │   ├── chat.py       # /v1/chat/completions
│   │   └── models.py     # /v1/models
├── schemas/
│   ├── openai/           # New directory
│   │   ├── __init__.py
│   │   ├── requests.py   # OpenAI request schemas
│   │   └── responses.py  # OpenAI response schemas
├── services/
│   ├── openai/           # New directory
│   │   ├── __init__.py
│   │   ├── translator.py # Request/response translation
│   │   └── streaming.py  # SSE format conversion
```

**Key Design Decisions:**
1. **Separate Route Namespace**: Use `/v1` prefix for OpenAI endpoints, keep `/api/v1` for native
2. **Translation Service**: Centralize conversion logic, don't pollute existing services
3. **Streaming Adapter**: Async generator wrapper to transform events
4. **Model Registry**: Configuration-driven model name mapping
5. **Feature Flags**: Enable/disable OpenAI compatibility via config

### Implementation Phases

**Phase 1 - MVP (3-4 days):**
- POST `/v1/chat/completions` endpoint (streaming + non-streaming)
- Basic request translation (messages → prompt)
- Basic response translation (content → OpenAI format)
- Model name mapping
- Authentication translation
- Error format translation
- Unit tests for translation logic
- Integration tests with OpenAI Python client

**Phase 2 - Tools (1-2 days):**
- Tool definition translation
- Tool calling in OpenAI format
- Tool result mapping
- Tests for tool scenarios

**Phase 3 - Polish (1 day):**
- GET `/v1/models` endpoint
- Advanced parameter support
- Performance optimization
- Documentation and examples

### Testing Strategy

**Unit Tests:**
- Request translation: messages → QueryRequest
- Response translation: SingleQueryResponse → OpenAI format
- Streaming translation: SSE event → OpenAI chunk
- Model name mapping
- Authentication mapping
- Error format conversion

**Integration Tests:**
- Full request/response cycle via OpenAI client
- Streaming with real SSE connection
- Error scenarios
- Authentication validation
- Rate limiting

**Contract Tests:**
- Validate OpenAI schema compliance
- Compare with official OpenAI API responses
- Ensure client compatibility

**E2E Tests:**
- Python `openai` client integration
- JavaScript OpenAI client integration
- Streaming scenarios
- Multi-turn conversations

## Related Specs

### Existing Specs

Scanning `./specs/` directory reveals only the current spec (`openai-api`). No prior specs exist in the repository based on glob results.

**Related Domain Areas:**
- API endpoint design (affects routing structure)
- Schema validation (new Pydantic models)
- Authentication (header mapping)
- Streaming (SSE format translation)

**No Conflicting Specs:**
Since this is an additive feature (new endpoints), no existing specs conflict.

**May Need Updates:**
- Documentation will need updating to describe dual API support
- OpenAPI specification will need OpenAI endpoints documented
- Rate limiting configuration may need per-endpoint tuning

## Quality Commands

Based on analysis of `pyproject.toml` and `Makefile`:

| Type | Command | Source |
|------|---------|--------|
| Lint | `uv run ruff check .` | Makefile: lint target |
| Format | `uv run ruff format .` | Makefile: fmt target |
| Type Check | `uv run ty check` | Makefile: typecheck target (using ty, not mypy) |
| Unit Test | `uv run pytest tests/unit -v` | Makefile: test-unit target |
| Integration Test | `uv run pytest tests/integration -v` | inferred from test structure |
| Contract Test | `uv run pytest tests/contract -v` | Makefile: test-fast target |
| Test (all) | `uv run pytest tests/ -v` | Makefile: test target |
| Test Coverage | `uv run pytest tests/ -v --cov=apps.api --cov-report=term-missing --cov-fail-under=80` | Makefile: test-cov target |
| Check All | `make check` | Makefile: check target (lint + typecheck) |

**Additional Commands:**
- Database migrations: `uv run alembic upgrade head`
- Dev server: `make dev` or `make dev-api`
- Clean cache: `make clean`

**Local CI Equivalent:**
```bash
uv run ruff check . && \
uv run ty check && \
uv run pytest tests/ -v --cov=apps.api --cov-fail-under=80
```

**Notes:**
- Tests use `pytest` with parallel execution (`-n auto`)
- Coverage target is 80%
- Type checking uses `ty` (Astral's fast type checker, NOT mypy)
- `ty` is configured for strict type checking in `pyproject.toml`

## Open Questions

1. **Message History Persistence**: Should we store full OpenAI message history in sessions, or reconstruct from SDK state?
   - **Recommendation**: Reconstruct from SDK - avoid duplicate state

2. **Model Name Strategy**: Fixed mapping (gpt-4 → sonnet) or configurable registry?
   - **Recommendation**: Configuration file for flexibility

3. **Token Limit Conversion**: How to map `max_tokens` to `max_turns`?
   - **SDK Research Finding**: Claude Agent SDK does NOT support max_tokens or temperature parameters
   - **Recommendation**: Ignore max_tokens completely (incompatible semantics - output tokens vs conversation turns)
   - **Implementation**: Accept parameter for compatibility, log warning, do NOT set max_turns

4. **Tool Format Support**: Implement in Phase 1 or defer to Phase 2?
   - **Recommendation**: Defer to Phase 2 for faster MVP

5. **Rate Limiting**: Same limits as native API or separate OpenAI limits?
   - **Recommendation**: Separate config keys, same default values initially

6. **Versioning**: Should we version the OpenAI compatibility layer?
   - **Recommendation**: No versioning initially, follow OpenAI's lead

7. **Breaking Changes**: What if OpenAI changes their API significantly?
   - **Recommendation**: Accept minor drift, document differences

8. **Performance Impact**: Will translation layer add significant latency?
   - **Recommendation**: Profile in Phase 1, optimize if needed

## Sources

### OpenAI API Documentation
- [Chat Completions API Reference](https://platform.openai.com/docs/api-reference/chat)
- [API Reference - OpenAI API](https://platform.openai.com/docs/api-reference/introduction)
- [Streaming API responses](https://platform.openai.com/docs/guides/streaming-responses)

### Implementation Examples
- [vLLM OpenAI-Compatible Server](https://docs.vllm.ai/en/latest/serving/openai_compatible_server/)
- [LiteLLM OpenAI-Compatible Endpoints](https://docs.litellm.ai/docs/providers/openai_compatible)
- [LM Studio OpenAI Compatibility](https://lmstudio.ai/docs/developer/openai-compat)

### Best Practices
- [OpenAI Compatibility - Together.ai](https://docs.together.ai/docs/openai-api-compatibility)
- [Cloudflare Workers AI OpenAI Compatibility](https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/)
- [BentoML OpenAI-compatible API](https://bentoml.com/llm/llm-inference-basics/openai-compatible-api)

### Technical Articles
- [Stream OpenAI responses with SSE | OpenFaaS](https://www.openfaas.com/blog/openai-streaming-responses/)
- [Server Sent Events in OpenAPI | Speakeasy](https://www.speakeasy.com/openapi/content/server-sent-events)

### Codebase Files
- `/mnt/cache/workspace/claude-agent-api/apps/api/main.py` - FastAPI app structure
- `/mnt/cache/workspace/claude-agent-api/apps/api/routes/query.py` - Current query endpoint
- `/mnt/cache/workspace/claude-agent-api/apps/api/schemas/requests/query.py` - QueryRequest schema
- `/mnt/cache/workspace/claude-agent-api/apps/api/schemas/responses.py` - Response schemas
- `/mnt/cache/workspace/claude-agent-api/apps/api/services/agent/service.py` - Agent service
- `/mnt/cache/workspace/claude-agent-api/pyproject.toml` - Project dependencies and config
- `/mnt/cache/workspace/claude-agent-api/Makefile` - Development commands

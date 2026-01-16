---
spec: openai-api
phase: requirements
created: 2026-01-14T16:00:00Z
---

# Requirements: OpenAI API Compatibility

## Goal

Enable the Claude Agent API to accept OpenAI-compatible requests at `/v1/chat/completions`, allowing existing tools and clients to seamlessly integrate with our API through a transparent translation layer that maps OpenAI's message-based format to Claude Agent SDK's prompt-based model.

## User Stories

### US-1: Basic Chat Completion (Non-Streaming)
**As a** developer using an OpenAI client library
**I want to** send chat completion requests to `/v1/chat/completions`
**So that** I can use the Claude Agent API without modifying my existing OpenAI integration code

**Acceptance Criteria:**
- [ ] AC-1.1: Given a POST request to `/v1/chat/completions` with `{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}`, when the request is processed, then the response matches OpenAI's non-streaming format with `id`, `object`, `created`, `model`, `choices`, and `usage` fields
- [ ] AC-1.2: Given messages with roles `system`, `user`, and `assistant`, when translated to QueryRequest, then system messages are extracted as `system_prompt` and other messages are joined into a single `prompt` string with role prefixes
- [ ] AC-1.3: Given an OpenAI model name mapping (gpt-4 → sonnet, gpt-3.5-turbo → haiku, gpt-4o → opus), when the request is translated, then the correct Claude model is used internally
- [ ] AC-1.4: Given a successful response from the agent service, when mapped to OpenAI format, then `choices[0].message.content` contains the text from all text content blocks concatenated
- [ ] AC-1.5: Given token usage data from the agent service, when mapped to OpenAI format, then `usage.prompt_tokens`, `usage.completion_tokens`, and `usage.total_tokens` are correctly populated

### US-2: Streaming Chat Completion
**As a** developer building a chat interface
**I want to** receive streaming responses via Server-Sent Events
**So that** I can display partial responses to users in real-time

**Acceptance Criteria:**
- [ ] AC-2.1: Given a request with `"stream": true`, when processed, then the response uses SSE format with `data: {json}\n` for each chunk
- [ ] AC-2.2: Given streaming is enabled, when the first event is sent, then it contains `{"choices": [{"delta": {"role": "assistant"}, "finish_reason": null}]}`
- [ ] AC-2.3: Given partial message events from the agent service, when translated, then each chunk contains `{"choices": [{"delta": {"content": "text"}, "finish_reason": null}]}`
- [ ] AC-2.4: Given the stream completes successfully, when the final event is sent, then it contains `{"choices": [{"delta": {}, "finish_reason": "stop"}]}`
- [ ] AC-2.5: Given the stream completes, when all events are sent, then a final `data: [DONE]\n` marker is emitted
- [ ] AC-2.6: Given a mid-stream error, when the error occurs, then an error chunk is sent with appropriate OpenAI error format before closing the stream

### US-3: Authentication Compatibility
**As a** developer using the OpenAI Python client
**I want to** authenticate using `Authorization: Bearer <token>` header
**So that** I can use standard OpenAI client configuration without custom header mappings

**Acceptance Criteria:**
- [ ] AC-3.1: Given a request with `Authorization: Bearer <token>` header, when validated, then the token is extracted and used for authentication
- [ ] AC-3.2: Given a request with `X-API-Key` header, when validated, then it continues to work (backward compatibility)
- [ ] AC-3.3: Given a request with neither header, when validation runs, then a 401 error is returned with OpenAI-compatible error format
- [ ] AC-3.4: Given an invalid bearer token, when validation fails, then a 401 error with OpenAI error object is returned

### US-4: Parameter Translation
**As a** developer configuring chat completions
**I want to** use OpenAI parameters (temperature, max_tokens, top_p)
**So that** I can control model behavior using familiar parameters

**SDK Research Finding**: Claude Agent SDK does NOT support temperature, top_p, max_tokens, or stop parameters. These will be accepted for compatibility but logged as unsupported.

**Acceptance Criteria:**
- [ ] AC-4.1: Given `"temperature": 0.7` in the request, when translated, then it is accepted but logged at WARNING level with message "Parameter temperature not supported by Claude Agent SDK"
- [ ] AC-4.2: Given `"max_tokens": 1000` in the request, when translated, then it is accepted but ignored completely (NOT mapped to max_turns due to incompatible semantics) and logged at WARNING level
- [ ] AC-4.3: Given `"top_p": 0.9` in the request, when translated, then it is accepted but logged as unsupported at WARNING level
- [ ] AC-4.4: Given unsupported parameters (e.g., `frequency_penalty`, `presence_penalty`, `stop`), when encountered, then they are logged at WARNING level but do not cause request failure
- [ ] AC-4.5: Given `"user": "user-123"` in the request, when translated, then it is mapped to the QueryRequest `user` field for tracking (SUPPORTED by SDK)

### US-5: Error Format Translation
**As a** developer handling API errors
**I want to** receive errors in OpenAI format
**So that** my error handling code works without modifications

**Acceptance Criteria:**
- [ ] AC-5.1: Given an internal API error, when returned, then the response contains an `error` object with `message`, `type`, and `code` fields matching OpenAI's schema
- [ ] AC-5.2: Given a validation error (e.g., missing required field), when returned, then the HTTP status is 400 and error type is "invalid_request_error"
- [ ] AC-5.3: Given an authentication error, when returned, then the HTTP status is 401 and error type is "authentication_error"
- [ ] AC-5.4: Given a rate limit error, when returned, then the HTTP status is 429 and error type is "rate_limit_exceeded"
- [ ] AC-5.5: Given an internal server error, when returned, then the HTTP status is 500 and error type is "api_error"

### US-6: Model Listing Endpoint
**As a** developer discovering available models
**I want to** call `GET /v1/models`
**So that** I can see what models are available and their capabilities

**Acceptance Criteria:**
- [ ] AC-6.1: Given a GET request to `/v1/models`, when processed, then the response contains a list of model objects with `id`, `object`, `created`, and `owned_by` fields
- [ ] AC-6.2: Given the model list, when returned, then it includes OpenAI-style names: "gpt-4" (maps to sonnet), "gpt-3.5-turbo" (maps to haiku), "gpt-4o" (maps to opus)
- [ ] AC-6.3: Given a GET request to `/v1/models/{model_id}`, when a valid model ID is provided, then details for that specific model are returned
- [ ] AC-6.4: Given a GET request to `/v1/models/{model_id}`, when an invalid model ID is provided, then a 404 error with OpenAI format is returned

### US-7: Tool Calling Support (Phase 2)
**As a** developer building agentic applications
**I want to** define tools using OpenAI's tool format
**So that** the agent can call external functions during conversation

**Acceptance Criteria:**
- [ ] AC-7.1: Given a request with `"tools": [{"type": "function", "function": {"name": "get_weather", "parameters": {...}}}]`, when translated, then it is mapped to the agent service's tool format
- [ ] AC-7.2: Given the agent calls a tool, when responding, then the response includes `{"choices": [{"message": {"tool_calls": [{"id": "...", "type": "function", "function": {"name": "...", "arguments": "..."}}]}}]}`
- [ ] AC-7.3: Given `"tool_choice": "auto"` in the request, when translated, then the agent decides when to use tools
- [ ] AC-7.4: Given `"tool_choice": "none"` in the request, when translated, then tools are disabled for this interaction
- [ ] AC-7.5: Given `"tool_choice": {"type": "function", "function": {"name": "specific_tool"}}`, when translated, then only that specific tool is enabled

## Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|----------|---------------------|
| FR-1 | Implement POST `/v1/chat/completions` endpoint | Must Have | Endpoint accepts OpenAI request schema and returns OpenAI response schema (verify with integration test using OpenAI Python client) |
| FR-2 | Implement request translation service | Must Have | `OpenAITranslator.translate_request()` converts OpenAI ChatCompletionRequest to QueryRequest (verify with unit tests covering all parameter mappings) |
| FR-3 | Implement response translation service | Must Have | `OpenAITranslator.translate_response()` converts SingleQueryResponse to OpenAI ChatCompletion format (verify with unit tests validating all required fields) |
| FR-4 | Implement streaming translation service | Must Have | `OpenAIStreamingAdapter` wraps agent service event stream and yields OpenAI-format chunks (verify with integration test asserting SSE format compliance) |
| FR-5 | Support both streaming and non-streaming modes | Must Have | Endpoint handles `stream: true/false` parameter correctly (verify both modes work with OpenAI client) |
| FR-6 | Implement model name mapping | Must Have | Configuration file maps OpenAI model names to Claude model names (verify with test asserting gpt-4 → sonnet, gpt-3.5-turbo → haiku, gpt-4o → opus) |
| FR-7 | Implement Bearer token authentication | Must Have | Extract token from `Authorization: Bearer <token>` header and validate (verify 401 for invalid tokens) |
| FR-8 | Implement OpenAI error format translation | Must Have | All errors returned in OpenAI error schema with correct status codes (verify error handler converts APIError to OpenAI format) |
| FR-9 | Implement GET `/v1/models` endpoint | Should Have | Return list of available models in OpenAI format (verify response matches OpenAI schema) |
| FR-10 | Implement GET `/v1/models/{model_id}` endpoint | Should Have | Return details for specific model (verify 404 for unknown models) |
| FR-11 | Accept temperature parameter | Should Have | Accept `temperature` for compatibility, log WARNING that SDK doesn't support it (verify log output in test) |
| FR-12 | Accept max_tokens parameter | Should Have | Accept `max_tokens` for compatibility, ignore completely (do NOT map to max_turns), log WARNING (verify no max_turns set in test) |
| FR-13 | Support user identifier parameter | Should Have | Map `user` to QueryRequest user field (verify tracking in logs) |
| FR-14 | Log unsupported parameters | Should Have | Structured logging at WARNING level for unimplemented parameters (verify log entries with test) |
| FR-15 | Implement tool calling translation | Could Have | Translate OpenAI tool format to agent service tool format (defer to Phase 2) |
| FR-16 | Support tool_choice parameter | Could Have | Map `tool_choice` to agent service configuration (defer to Phase 2) |
| FR-17 | Support top_p parameter | Could Have | Pass `top_p` to agent service if supported (verify or log unsupported) |
| FR-18 | Support stop sequences | Could Have | Map `stop` parameter to agent service (may not be supported by SDK) |
| FR-19 | Support response_format parameter | Could Have | Handle `{"type": "json_object"}` for JSON mode (may map to structured output) |
| FR-20 | Support n parameter (multiple completions) | Won't Have | Not supported - always return single completion (document limitation) |
| FR-21 | Support logprobs parameter | Won't Have | Not exposed by Claude Agent SDK (document limitation) |
| FR-22 | Support logit_bias parameter | Won't Have | Not supported by Claude models (document limitation) |
| FR-23 | Support seed parameter | Won't Have | Not supported for deterministic sampling (document limitation) |

## Non-Functional Requirements

| ID | Requirement | Metric | Target |
|----|-------------|--------|--------|
| NFR-1 | Type Safety | Zero `Any` types | All translation functions fully typed with `TypedDict` for JSON structures |
| NFR-2 | Test Coverage | Line coverage percentage | ≥80% for translation services, ≥90% for request/response schemas |
| NFR-3 | Translation Latency | P95 latency overhead | <5ms for request translation, <10ms for response translation |
| NFR-4 | Streaming Overhead | First token time | <50ms delay from agent service event to OpenAI SSE chunk emission |
| NFR-5 | Error Handling | Error translation accuracy | 100% of internal errors mapped to correct OpenAI error types and status codes |
| NFR-6 | Backward Compatibility | Existing endpoint impact | Zero changes to `/api/v1/query` endpoint behavior or response format |
| NFR-7 | Authentication | Security equivalence | Bearer token auth provides same security as existing X-API-Key auth |
| NFR-8 | Documentation | Endpoint documentation | OpenAPI spec updated with all `/v1/*` endpoints and schemas |
| NFR-9 | Code Quality | Linting and formatting | Zero ruff violations, 100% ty type check pass rate (ty is primary type checker, NOT mypy) |
| NFR-10 | Maintainability | Isolation | Translation logic isolated in `apps/api/routes/openai/` and `apps/api/services/openai/` |

## Glossary

- **OpenAI API**: Industry-standard LLM inference API originally created by OpenAI, now a de facto standard
- **Chat Completion**: OpenAI's primary API endpoint for conversational AI interactions
- **SSE (Server-Sent Events)**: HTTP streaming protocol for server-to-client push notifications
- **Message Array**: OpenAI's conversation format using array of `{role, content}` objects
- **Content Block**: Claude Agent SDK's structured response format (text, thinking, tool_use, tool_result)
- **Translation Layer**: Service that converts between OpenAI format and internal QueryRequest/Response format
- **Model Mapping**: Configuration that maps OpenAI model names (gpt-4) to Claude models (sonnet)
- **Bearer Token**: HTTP authentication scheme using `Authorization: Bearer <token>` header
- **Delta**: Incremental content in streaming responses (OpenAI's streaming format)
- **Finish Reason**: Enumeration indicating why generation stopped (stop, length, tool_calls, error)
- **Tool Calling**: Function calling capability where LLM can invoke external tools/functions
- **max_tokens**: OpenAI parameter limiting total tokens generated
- **max_turns**: Claude Agent SDK parameter limiting conversation turns (1 turn = user + assistant exchange)
- **TypedDict**: Python type hint for dictionaries with specific key-value types (no `Any` allowed)

## Out of Scope

The following are explicitly excluded from this implementation:

- **OpenAI Embeddings API** (`/v1/embeddings`) - Different capability, separate feature
- **OpenAI Assistants API** (`/v1/assistants`) - Complex stateful API, not compatible with agent architecture
- **OpenAI Fine-tuning API** (`/v1/fine-tunes`) - Model training not applicable to Claude Agent SDK
- **OpenAI Moderation API** (`/v1/moderations`) - Content moderation handled separately
- **Legacy Completions API** (`/v1/completions`) - Deprecated by OpenAI, focus on chat completions
- **Image Generation** (`/v1/images`) - Not supported by Claude models
- **Audio Transcription/Translation** (`/v1/audio/*`) - Different modality, separate feature
- **Batch API** (`/v1/batches`) - Async batch processing not in MVP scope
- **Vision Input in Messages**: While QueryRequest supports images, OpenAI message format with image URLs is deferred to future enhancement
- **Function/Tool Result Messages**: Phase 1 excludes tool calling, deferred to Phase 2
- **Multi-turn History Management**: Translation uses simple concatenation; sophisticated conversation management deferred
- **Response Caching Headers**: OpenAI's prompt caching via headers not implemented initially
- **Organization/Project Identifiers**: OpenAI's multi-tenant headers not applicable to single-deployment architecture

## Dependencies

**Internal Dependencies:**
- Existing QueryRequest schema and validation logic (`apps/api/schemas/requests/query.py`)
- Existing SingleQueryResponse schema (`apps/api/schemas/responses.py`)
- Agent service streaming implementation (`apps/api/services/agent/service.py`)
- SSE event infrastructure (`sse-starlette` package)
- Authentication dependency injection (`apps/api/dependencies.py`)
- Error handling framework (`apps/api/exceptions.py`)

**External Dependencies:**
- No new package dependencies required
- Claude Agent SDK behavior (cannot modify SDK, must adapt to its interfaces)
- Existing PostgreSQL session storage schema
- Existing Redis caching implementation

**Configuration Dependencies:**
- Model name mapping configuration file (new: `config/openai_models.yaml`)
- Rate limiting configuration may need separate keys for `/v1/*` endpoints
- Feature flag to enable/disable OpenAI compatibility (environment variable)

**Documentation Dependencies:**
- OpenAPI specification needs updating with `/v1/*` endpoints
- README needs section on OpenAI compatibility usage
- Migration guide for clients switching from OpenAI to Claude Agent API

## Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Message History Reconstruction**: OpenAI expects full conversation history, but SDK manages state internally | High | Medium | Use session_id for state continuity, document limitation that message history cannot be arbitrarily replayed |
| **Parameter Incompatibility**: Some OpenAI parameters have no Claude equivalent (logprobs, seed, logit_bias) | Medium | High | Document unsupported parameters, log warnings, provide clear error messages when critical parameters are missing |
| **Token-to-Turn Conversion**: `max_tokens` → `max_turns` conversion has incompatible semantics (output tokens vs conversation turns) | Medium | High | **SDK Research Resolved**: Ignore max_tokens completely, do NOT map to max_turns. Accept parameter, log warning, proceed without limit |
| **Streaming Format Mismatch**: OpenAI delta format differs from agent service events (partial vs full content blocks) | Medium | Medium | Implement stateful streaming adapter that tracks deltas, test thoroughly with long responses |
| **Tool Format Complexity**: OpenAI tool schema differs significantly from Claude Agent SDK tools | High | Medium | Defer to Phase 2, ensure Phase 1 architecture supports future tool translation |
| **Performance Overhead**: Translation layer adds latency to request/response path | Low | Medium | Profile translation functions, optimize hot paths, consider caching model mappings |
| **Authentication Security**: Bearer token extraction must maintain security equivalence | High | Low | Reuse existing auth validation logic, add comprehensive security tests |
| **Breaking Changes in OpenAI API**: OpenAI may update their API schema | Medium | Low | Version our implementation separately, document compatibility target (e.g., "OpenAI API v1 as of 2026-01") |
| **Type Safety Violations**: Complex JSON translation may introduce `Any` types | Medium | Medium | ZERO `Any` types enforced: ty strict checking, TypedDict for all JSON structures (extend apps/api/types.py), Pydantic for request validation only |
| **Session State Confusion**: Session management differs between OpenAI (stateless) and Claude Agent SDK (stateful) | High | Medium | Document session behavior clearly, ensure session_id handling is correct in both streaming/non-streaming modes |

## Success Criteria

The implementation is considered successful when:

1. **OpenAI Client Integration**: The official OpenAI Python client (`openai>=1.0.0`) can successfully interact with `/v1/chat/completions` by only changing `base_url` parameter

   ```python
   from openai import OpenAI
   client = OpenAI(base_url="http://localhost:54000/v1", api_key="test-key")
   response = client.chat.completions.create(
       model="gpt-4",
       messages=[{"role": "user", "content": "Hello"}]
   )
   assert response.choices[0].message.content is not None
   ```

2. **Streaming Compliance**: Streaming responses match OpenAI SSE format exactly, verifiable by comparing with official OpenAI API responses using identical prompts

3. **Error Handling Parity**: All error scenarios (authentication, validation, rate limiting, server errors) return OpenAI-compatible error responses that existing error handlers can process

4. **Test Coverage Achievement**:
   - Translation services: ≥80% line coverage
   - Request/response schemas: ≥90% line coverage
   - Integration tests verify end-to-end OpenAI client compatibility

5. **Type Safety Enforcement**:
   - `uv run ty check` passes with zero errors
   - `uv run ruff check --select=ANN401` reports zero `Any` type violations
   - All JSON structures use explicit `TypedDict` definitions

6. **Performance Acceptance**:
   - P95 request translation latency: <5ms
   - P95 response translation latency: <10ms
   - Streaming first token overhead: <50ms
   - No degradation to existing `/api/v1/query` endpoint performance

7. **Documentation Completeness**:
   - OpenAPI spec includes all `/v1/*` endpoints with examples
   - README includes "OpenAI Compatibility" section with usage examples
   - Unsupported parameters are clearly documented with rationale

8. **Backward Compatibility**:
   - All existing tests for `/api/v1/*` endpoints continue to pass
   - No changes to existing API behavior or response formats
   - Both `X-API-Key` and `Authorization: Bearer` authentication work concurrently

9. **Phase 1 Scope Completion**:
   - ✓ POST `/v1/chat/completions` (streaming + non-streaming)
   - ✓ Authentication translation (Bearer token)
   - ✓ Model name mapping (gpt-4/3.5-turbo/4o)
   - ✓ Error format translation
   - ✓ Basic parameter support (user parameter ONLY - temperature, max_tokens, top_p, stop NOT supported by SDK, accept and log warnings)
   - ✓ GET `/v1/models` (should have, nice to have)

10. **Quality Gates**:
    - All tests pass: `uv run pytest tests/`
    - Linting passes: `uv run ruff check .`
    - Type checking passes: `uv run ty check` (ty is primary type checker)
    - Coverage target met: `uv run pytest --cov=apps.api --cov-fail-under=80`

## Implementation Phases

### Phase 1: MVP - Basic Chat Completions (Must Have)
**Scope:** Core functionality for text-based chat completions without tools

**Deliverables:**
1. OpenAI request/response schemas (`apps/api/schemas/openai/`)
2. Translation services (`apps/api/services/openai/translator.py`, `streaming.py`)
3. Chat completions endpoint (`apps/api/routes/openai/chat.py`)
4. Models endpoint (`apps/api/routes/openai/models.py`)
5. Authentication adapter for Bearer tokens
6. Error format translation
7. Model name mapping configuration
8. Unit tests for all translation logic
9. Integration tests with OpenAI Python client
10. Updated OpenAPI specification

**User Stories:** US-1, US-2, US-3, US-4, US-5, US-6

**Success Criteria:** OpenAI Python client can perform basic chat completions (non-streaming and streaming) by only changing base_url

### Phase 2: Tool Calling Support (Should Have)
**Scope:** Function/tool calling capability

**Deliverables:**
1. Tool definition translation (OpenAI → Claude Agent SDK format)
2. Tool use response translation (content blocks → OpenAI tool_calls)
3. Tool result message handling
4. Enhanced streaming for tool calls
5. Tests for tool calling scenarios
6. Documentation updates for tool calling

**User Stories:** US-7

**Success Criteria:** OpenAI client can define functions and receive tool_calls in responses

### Phase 3: Advanced Features & Polish (Could Have)
**Scope:** Additional parameters, optimizations, documentation

**Deliverables:**
1. Additional parameter support (top_p, stop sequences, response_format)
2. Performance optimizations (caching, batching)
3. Enhanced error messages with helpful suggestions
4. Migration guide documentation
5. Example code for common use cases
6. Load testing and benchmarking
7. Security audit of translation layer

**Success Criteria:** Feature parity with OpenAI API for all supported parameters, comprehensive documentation for migration

## Validation Checklist

Before marking requirements as complete, verify:

- [ ] All user stories have concrete, testable acceptance criteria
- [ ] No ambiguous terms (e.g., "fast", "easy", "simple") in requirements
- [ ] Each functional requirement has clear priority (Must/Should/Could/Won't)
- [ ] All non-functional requirements have measurable metrics and targets
- [ ] Glossary defines all domain-specific terms used in requirements
- [ ] Out of scope section prevents scope creep
- [ ] Dependencies are identified with mitigation plans
- [ ] Risks include impact, probability, and mitigation strategies
- [ ] Success criteria are objective and measurable
- [ ] Type safety requirements enforce ZERO `Any` types policy
- [ ] Test coverage targets are specified (80%+ overall)
- [ ] Performance targets are quantified with metrics
- [ ] Backward compatibility is guaranteed for existing endpoints

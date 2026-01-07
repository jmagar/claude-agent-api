# Tasks: Claude Agent API

**Input**: Design documents from `/specs/001-claude-agent-api/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.yaml

**Tests**: Tests are included as this is a production API requiring full test coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **API service**: `apps/api/` with subdirectories per plan.md
- **Tests**: `tests/` with contract/, integration/, unit/ subdirectories
- **Migrations**: `alembic/` with versions/

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md in apps/api/
- [X] T002 Initialize Python project with pyproject.toml and uv dependencies
- [X] T003 [P] Configure ruff, mypy, and pytest in pyproject.toml
- [X] T004 [P] Create docker-compose.yaml with PostgreSQL (port 53432) and Redis (port 53380)
- [X] T005 [P] Create .env.example with required environment variables
- [X] T006 [P] Create tests/ directory structure with conftest.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create apps/api/config.py with pydantic-settings for configuration management
- [X] T008 [P] Create apps/api/protocols.py with Protocol interfaces (SessionRepository, Cache, AgentClient)
- [X] T009 [P] Create apps/api/types.py with TypedDicts and type aliases
- [X] T010 [P] Create apps/api/exceptions.py with custom exception classes (SessionNotFoundError, ValidationError, etc.)
- [X] T011 Setup Alembic configuration in alembic/alembic.ini and alembic/env.py
- [X] T012 Create apps/api/models/session.py with SQLAlchemy Session, SessionMessage, Checkpoint models
- [X] T013 Create Alembic migration for sessions, session_messages, checkpoints tables in alembic/versions/
- [X] T014 [P] Create apps/api/adapters/cache.py implementing Cache protocol with Redis
- [X] T015 Create apps/api/adapters/session_repo.py implementing SessionRepository protocol with SQLAlchemy
- [X] T016 [P] Create apps/api/middleware/correlation.py for correlation ID injection
- [X] T017 [P] Create apps/api/middleware/logging.py for structured request logging
- [X] T018 Create apps/api/dependencies.py with FastAPI dependency functions (get_db, get_cache, get_session_repo)
- [X] T019 Create apps/api/main.py with FastAPI app skeleton, middleware registration, router includes
- [X] T020 [P] Create apps/api/routes/health.py with /health endpoint
- [X] T021 Implement API key authentication middleware in apps/api/middleware/auth.py
- [X] T022 [P] Create tests/unit/test_config.py for configuration validation
- [X] T023 [P] Create tests/unit/test_exceptions.py for exception classes

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic Agent Query (Priority: P1)

**Goal**: Send a prompt to an AI agent and receive streamed responses via SSE

**Independent Test**: Send a single prompt and verify the agent completes a task, receiving init, message, and result events

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US1] Contract test for POST /query endpoint in tests/contract/test_query_contract.py
- [X] T025 [P] [US1] Contract test for POST /query/single endpoint in tests/contract/test_query_contract.py
- [X] T026 [P] [US1] Integration test for streaming query in tests/integration/test_query.py
- [X] T027 [P] [US1] Unit test for agent service in tests/unit/test_agent_service.py

### Implementation for User Story 1

- [X] T028 [P] [US1] Create apps/api/schemas/requests.py with QueryRequest schema (include cwd, env, max_turns fields per FR-031, FR-032, FR-033)
- [X] T029 [P] [US1] Create apps/api/schemas/responses.py with StreamEvent, InitEvent, MessageEvent, ResultEvent, ErrorEvent, DoneEvent schemas
- [X] T030 [P] [US1] Create apps/api/schemas/messages.py with ContentBlockSchema, UsageSchema mappings
- [X] T031 [US1] Create apps/api/services/agent.py with AgentService class wrapping ClaudeSDKClient
- [X] T032 [US1] Implement SSE streaming generator in apps/api/services/agent.py with bounded queue (covers FR-005a streaming input mode with AsyncGenerator)
- [X] T033 [US1] Create apps/api/routes/query.py with POST /query streaming endpoint using sse-starlette
- [X] T034 [US1] Implement POST /query/single endpoint in apps/api/routes/query.py
- [X] T035 [US1] Add client disconnect monitoring and cleanup in query routes
- [X] T036 [US1] Register query router in apps/api/main.py
- [X] T036a [US1] Add QuestionEvent schema to apps/api/schemas/responses.py for AskUserQuestion handling
- [X] T036b [US1] Implement POST /sessions/{id}/answer endpoint in apps/api/routes/sessions.py
- [X] T036c [P] [US1] Add UsageData schema to apps/api/schemas/messages.py with input_tokens, output_tokens, cache_read_input_tokens fields (FR-036)
- [X] T036d [US1] Include usage data in MessageEventData for streamed assistant messages (FR-036)
- [X] T036e [US1] Add total_cost_usd and model_usage breakdown fields to ResultEventData schema (FR-037, FR-038)

**Checkpoint**: Basic agent queries work - can send prompts and receive streamed responses

---

## Phase 4: User Story 2 - Session Management (Priority: P1)

**Goal**: Maintain conversation context across multiple interactions using session IDs

**Independent Test**: Send an initial query, capture session ID, send a follow-up query that references the first conversation

### Tests for User Story 2

- [X] T037 [P] [US2] Contract test for GET /sessions endpoint in tests/contract/test_sessions_contract.py
- [X] T038 [P] [US2] Contract test for GET /sessions/{id} endpoint in tests/contract/test_sessions_contract.py
- [X] T039 [P] [US2] Contract test for POST /sessions/{id}/resume endpoint in tests/contract/test_sessions_contract.py
- [X] T040 [P] [US2] Contract test for POST /sessions/{id}/fork endpoint in tests/contract/test_sessions_contract.py
- [X] T041 [P] [US2] Integration test for session resume in tests/integration/test_sessions.py
- [X] T042 [P] [US2] Unit test for session service in tests/unit/test_session_service.py

### Implementation for User Story 2

- [X] T043 [P] [US2] Add ResumeRequest schema to apps/api/schemas/requests.py
- [X] T044 [P] [US2] Add ForkRequest schema to apps/api/schemas/requests.py
- [X] T045 [P] [US2] Add SessionResponse, SessionListResponse schemas to apps/api/schemas/responses.py
- [X] T046 [US2] Create apps/api/services/session.py with SessionService class
- [X] T047 [US2] Implement session creation, retrieval, and update in SessionService
- [X] T048 [US2] Implement session caching in Redis via SessionService
- [X] T049 [US2] Create apps/api/routes/sessions.py with GET /sessions list endpoint
- [X] T050 [US2] Implement GET /sessions/{id} endpoint in apps/api/routes/sessions.py
- [X] T051 [US2] Implement POST /sessions/{id}/resume endpoint in apps/api/routes/sessions.py
- [X] T052 [US2] Implement POST /sessions/{id}/fork endpoint in apps/api/routes/sessions.py
- [X] T053 [US2] Implement POST /sessions/{id}/interrupt endpoint in apps/api/routes/sessions.py
- [X] T054 [US2] Add session_id parameter handling in query routes for resume flow
- [X] T055 [US2] Register sessions router in apps/api/main.py

**Checkpoint**: Sessions work - can resume and fork conversations with full context

---

## Phase 5: User Story 3 - Tool Configuration (Priority: P1)

**Goal**: Control which tools the agent can use per request

**Independent Test**: Configure allowed tools and verify the agent only uses permitted tools

### Tests for User Story 3

- [X] T056 [P] [US3] Integration test for tool restriction in tests/integration/test_tools.py
- [X] T057 [P] [US3] Unit test for tool configuration validation in tests/unit/test_schemas.py

### Implementation for User Story 3

- [X] T058 [US3] Add allowed_tools and disallowed_tools validation to QueryRequest schema
- [X] T059 [US3] Implement tool filtering in AgentService.create_options() in apps/api/services/agent.py
- [X] T060 [US3] Add built-in tools constant and validation in apps/api/types.py
- [X] T061 [US3] Document available tools in error messages when invalid tool requested

**Checkpoint**: Tool configuration works - can restrict agent capabilities per request

---

## Phase 6: User Story 4 - Custom Subagent Definition (Priority: P2)

**Goal**: Define specialized subagents that the main agent can delegate tasks to

**Independent Test**: Define a subagent programmatically and send a prompt that explicitly invokes it by name

### Tests for User Story 4

- [X] T062 [P] [US4] Integration test for subagent invocation in tests/integration/test_subagents.py
- [X] T063 [P] [US4] Unit test for AgentDefinitionSchema validation in tests/unit/test_schemas.py

### Implementation for User Story 4

- [X] T064 [US4] Add AgentDefinitionSchema to apps/api/schemas/requests.py with description, prompt, tools, model fields and Task tool restriction
- [X] T065 [US4] Implement agents parameter handling in AgentService.create_options()
- [X] T066 [US4] Add parent_tool_use_id field to MessageEventData for subagent context tracking
- [X] T067 [US4] Document subagent usage patterns in error messages

**Checkpoint**: Subagents work - can define and invoke specialized agents

---

## Phase 7: User Story 5 - MCP Server Integration (Priority: P2)

**Goal**: Extend agent capabilities by connecting external MCP servers

**Independent Test**: Configure an MCP server and verify the agent can use tools provided by that server

### Tests for User Story 5

- [ ] T068 [P] [US5] Integration test for MCP server connection in tests/integration/test_mcp.py
- [ ] T069 [P] [US5] Unit test for McpServerConfigSchema validation in tests/unit/test_schemas.py

### Implementation for User Story 5

- [ ] T070 [US5] Add McpServerConfigSchema to apps/api/schemas/requests.py with transport validation
- [ ] T071 [US5] Add McpServerStatus schema to apps/api/schemas/responses.py
- [ ] T072 [US5] Implement mcp_servers parameter handling in AgentService.create_options()
- [ ] T073 [US5] Add MCP server status reporting in InitEvent data
- [ ] T074 [US5] Implement environment variable resolution for ${VAR:-default} syntax

**Checkpoint**: MCP integration works - can connect external tool providers

---

## Phase 8: User Story 6 - Permission Control (Priority: P2)

**Goal**: Fine-grained control over what the agent can do with approval workflows

**Independent Test**: Set permission mode and verify tool approval behavior matches expectations

### Tests for User Story 6

- [ ] T075 [P] [US6] Integration test for permission modes in tests/integration/test_permissions.py
- [ ] T076 [P] [US6] Unit test for permission mode handling in tests/unit/test_agent_service.py

### Implementation for User Story 6

- [ ] T077 [US6] Add permission_mode enum and validation to QueryRequest schema
- [ ] T078 [US6] Implement permission_mode handling in AgentService.create_options()
- [ ] T079 [US6] Add permission_prompt_tool_name parameter support
- [ ] T080 [US6] Document permission modes in API response messages
- [ ] T080a [US6] Implement dynamic permission mode changes during streaming via SSE control events (FR-015)

**Checkpoint**: Permission control works - can govern tool approval per request

---

## Phase 9: User Story 7 - Hooks for Agent Lifecycle (Priority: P2)

**Goal**: Intercept agent execution at key points via HTTP webhooks

**Independent Test**: Register a PreToolUse hook and verify it executes before tool calls

### Tests for User Story 7

- [ ] T081 [P] [US7] Integration test for webhook hooks in tests/integration/test_hooks.py
- [ ] T082 [P] [US7] Unit test for HooksConfigSchema validation in tests/unit/test_schemas.py
- [ ] T083 [P] [US7] Unit test for webhook service in tests/unit/test_webhook_service.py

### Implementation for User Story 7

- [ ] T084 [US7] Add HooksConfigSchema and HookWebhookSchema to apps/api/schemas/requests.py
- [ ] T085 [US7] Create apps/api/services/webhook.py with WebhookService for HTTP callbacks
- [ ] T086 [US7] Implement hook callback execution with timeout, error handling, and input transformation support (FR-020: allow/deny/ask responses with optional transformed input)
- [ ] T087 [US7] Implement hooks integration in AgentService using SDK hooks parameter
- [ ] T088 [US7] Add matcher regex support for tool name filtering
- [ ] T088a [US7] Implement SubagentStop hook type for tracking subagent completion (FR-021)
- [ ] T088b [US7] Implement Stop hook type for agent completion events (FR-022)
- [ ] T088c [US7] Implement UserPromptSubmit hook type for prompt interception (FR-023)

**Checkpoint**: Hooks work - can intercept agent execution for custom logic

---

## Phase 10: User Story 8 - Structured Output (Priority: P3)

**Goal**: Return agent data in a specific JSON schema format

**Independent Test**: Provide a JSON schema and verify the agent's final output validates against it

### Tests for User Story 8

- [ ] T089 [P] [US8] Integration test for structured output in tests/integration/test_structured_output.py
- [ ] T090 [P] [US8] Unit test for OutputFormatSchema validation in tests/unit/test_schemas.py

### Implementation for User Story 8

- [ ] T091 [US8] Add OutputFormatSchema to apps/api/schemas/requests.py with schema validation
- [ ] T092 [US8] Implement output_format parameter handling in AgentService.create_options()
- [ ] T093 [US8] Add structured_output field to ResultEventData schema
- [ ] T094 [US8] Add JSON schema validation error handling

**Checkpoint**: Structured output works - can enforce output format per request

---

## Phase 11: User Story 9 - File Checkpointing and Rewind (Priority: P3)

**Goal**: Track file changes made by the agent and revert to previous states

**Independent Test**: Enable checkpointing, have the agent modify files, then rewind and verify restoration

### Tests for User Story 9

- [ ] T095 [P] [US9] Contract test for GET /sessions/{id}/checkpoints endpoint in tests/contract/test_checkpoints_contract.py
- [ ] T096 [P] [US9] Contract test for POST /sessions/{id}/rewind endpoint in tests/contract/test_checkpoints_contract.py
- [ ] T097 [P] [US9] Integration test for file rewind in tests/integration/test_checkpoints.py
- [ ] T098 [P] [US9] Unit test for checkpoint service in tests/unit/test_checkpoint_service.py

### Implementation for User Story 9

- [ ] T099 [US9] Add CheckpointResponse, CheckpointListResponse, RewindRequest schemas to apps/api/schemas/responses.py
- [ ] T100 [US9] Implement enable_file_checkpointing parameter handling in AgentService
- [ ] T101 [US9] Create apps/api/services/checkpoint.py with CheckpointService class
- [ ] T102 [US9] Implement GET /sessions/{id}/checkpoints endpoint in apps/api/routes/sessions.py
- [ ] T103 [US9] Implement POST /sessions/{id}/rewind endpoint in apps/api/routes/sessions.py
- [ ] T104 [US9] Add checkpoint UUID tracking in message stream processing

**Checkpoint**: File checkpointing works - can track and revert file changes

---

## Phase 12: User Story 10 - Model Selection (Priority: P3)

**Goal**: Choose which Claude model powers the agent, balancing cost and capability

**Independent Test**: Specify different models and verify responses come from the requested model

### Tests for User Story 10

- [ ] T105 [P] [US10] Integration test for model selection in tests/integration/test_model_selection.py
- [ ] T106 [P] [US10] Unit test for model validation in tests/unit/test_schemas.py

### Implementation for User Story 10

- [ ] T107 [US10] Add model parameter validation to QueryRequest schema
- [ ] T108 [US10] Implement model parameter handling in AgentService.create_options()
- [ ] T109 [US10] Add model information to InitEvent and ResultEvent responses
- [ ] T110 [US10] Add model_usage breakdown in ResultEventData for multi-model sessions

**Checkpoint**: Model selection works - can choose model per request

---

## Phase 13: Advanced Features

**Purpose**: Additional SDK features and enhancements

### Plugins, Skills, and Slash Commands

- [ ] T111 [P] Add SdkPluginConfigSchema to apps/api/schemas/requests.py
- [ ] T112 [P] Add SandboxSettingsSchema to apps/api/schemas/requests.py
- [ ] T113 Implement plugins parameter handling in AgentService.create_options()
- [ ] T114 Implement setting_sources parameter handling for CLAUDE.md loading
- [ ] T115 Add commands list to InitEvent for slash command discovery
- [ ] T115a Implement slash command prefix detection in prompt processing in apps/api/services/agent.py
- [ ] T116 Implement system_prompt_append (preset+append mode) handling

### Skills

- [ ] T116a Add SkillDiscoveryResponse schema to apps/api/schemas/responses.py
- [ ] T116b Implement GET /skills endpoint for skill discovery in apps/api/routes/skills.py
- [ ] T116c Implement Skill tool allowedTools validation in apps/api/services/agent.py

### TODO Tracking

- [ ] T116d Add TodoEventData schema to apps/api/schemas/responses.py
- [ ] T116e Implement TodoWrite tool use message streaming in apps/api/services/agent.py

### Partial Messages and WebSocket

- [ ] T117 Add PartialMessageEvent and ContentDeltaSchema to apps/api/schemas/responses.py
- [ ] T118 Implement include_partial_messages streaming support in AgentService
- [ ] T119 Create apps/api/routes/websocket.py for /query/ws WebSocket endpoint
- [ ] T120 Implement WebSocket message handling for prompt, interrupt types

### Image Support

- [ ] T121 Add ImageContentSchema to apps/api/schemas/requests.py
- [ ] T122 Implement images parameter handling in AgentService for multimodal prompts

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T123 Run all contract tests against OpenAPI spec in tests/contract/test_openapi.py
- [ ] T124 Add rate limiting with slowapi in apps/api/middleware/ratelimit.py
- [ ] T125 [P] Add request timeout handling in all routes
- [ ] T126 [P] Add comprehensive error response formatting
- [ ] T127 [P] Add OpenAPI documentation generation and validation
- [ ] T128 Security hardening - validate all inputs, prevent injection attacks
- [ ] T129 Run quickstart.md validation - verify all setup steps work
- [ ] T130 Performance testing - verify 100 concurrent sessions, <2s time-to-first-token, p95 latency <500ms, error rate <1% (track 5xx responses and timeout errors during load test)
- [ ] T131 Add graceful shutdown handling for active sessions
- [ ] T132 Final mypy strict mode check - no type errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-12)**: All depend on Foundational phase completion
  - P1 Stories (US1-US3) can proceed in parallel after Foundational
  - P2 Stories (US4-US7) can proceed in parallel after Foundational
  - P3 Stories (US8-US10) can proceed in parallel after Foundational
- **Advanced Features (Phase 13)**: Depends on US1 (Basic Query) completion
- **Polish (Phase 14)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Basic Query - No dependencies on other stories
- **User Story 2 (P1)**: Session Management - Can integrate with US1 endpoints
- **User Story 3 (P1)**: Tool Configuration - Extends US1 schemas
- **User Story 4 (P2)**: Subagents - Requires Task tool from US3
- **User Story 5 (P2)**: MCP Servers - Independent of other P2 stories
- **User Story 6 (P2)**: Permissions - Independent of other P2 stories
- **User Story 7 (P2)**: Hooks - Independent of other P2 stories
- **User Story 8 (P3)**: Structured Output - Independent
- **User Story 9 (P3)**: Checkpointing - Requires US2 sessions
- **User Story 10 (P3)**: Model Selection - Independent

### Within Each User Story

- Tests (TDD) MUST be written and FAIL before implementation
- Schemas before services
- Services before routes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for POST /query endpoint in tests/contract/test_query_contract.py"
Task: "Contract test for POST /query/single endpoint in tests/contract/test_query_contract.py"
Task: "Integration test for streaming query in tests/integration/test_query.py"
Task: "Unit test for agent service in tests/unit/test_agent_service.py"

# Launch all schema tasks for User Story 1 together:
Task: "Create apps/api/schemas/requests.py with QueryRequest schema"
Task: "Create apps/api/schemas/responses.py with StreamEvent, InitEvent, MessageEvent, ResultEvent schemas"
Task: "Create apps/api/schemas/messages.py with ContentBlockSchema, UsageSchema mappings"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic Query)
4. **STOP and VALIDATE**: Test basic queries independently
5. Complete Phase 4: User Story 2 (Sessions)
6. Complete Phase 5: User Story 3 (Tool Config)
7. **Deploy/Demo MVP**: Basic agent API with sessions and tool control

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Basic Query) → Test independently → Core API works (MVP-1!)
3. Add US2 (Sessions) + US3 (Tools) → Test independently → Full P1 features (MVP-2!)
4. Add US4-US7 (P2 features) → Test independently → Enterprise features
5. Add US8-US10 (P3 features) → Test independently → Complete feature parity
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Basic Query)
   - Developer B: User Story 2 (Sessions)
   - Developer C: User Story 3 (Tools)
3. After P1 complete:
   - Developer A: User Story 4 + 5 (Subagents, MCP)
   - Developer B: User Story 6 + 7 (Permissions, Hooks)
   - Developer C: User Story 8 + 9 + 10 (P3 features)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (RED-GREEN-REFACTOR)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All paths are relative to repository root
- Strict typing required - mypy strict mode, no Any types

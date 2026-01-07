# Feature Specification: Claude Agent API

**Feature Branch**: `001-claude-agent-api`
**Created**: 2026-01-06
**Status**: Draft
**Input**: User description: "Create an API that can leverage the full capabilities of the Claude Agent SDK with FULL feature parity"

## Overview

This specification defines an HTTP API service that wraps the Claude Agent SDK, exposing all SDK capabilities through RESTful endpoints and real-time streaming connections. The API enables developers to build applications powered by autonomous Claude agents without directly integrating the SDK.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Agent Query (Priority: P1)

A developer wants to send a prompt to an AI agent and receive responses, with the agent autonomously using tools to complete tasks.

**Why this priority**: This is the core functionality - without basic query capability, no other features matter. It delivers immediate value by enabling autonomous AI agent interactions.

**Independent Test**: Can be fully tested by sending a single prompt and verifying the agent completes a task using tools (e.g., "List files in this directory").

**Acceptance Scenarios**:

1. **Given** a valid API key and prompt, **When** the user sends a query request, **Then** the system returns streamed messages showing agent progress and final result.
2. **Given** a prompt requiring tool use, **When** the agent needs to read a file, **Then** the system executes the built-in Read tool and includes the result in the response stream.
3. **Given** an invalid API key, **When** the user sends a query request, **Then** the system returns an authentication error with appropriate error code.

---

### User Story 2 - Session Management (Priority: P1)

A developer wants to maintain conversation context across multiple interactions, allowing the agent to remember previous exchanges.

**Why this priority**: Sessions enable stateful conversations which are essential for complex multi-turn workflows. Without sessions, each query is isolated and cannot build on previous context.

**Independent Test**: Can be tested by sending an initial query, capturing the session ID, then sending a follow-up query that references the first conversation.

**Acceptance Scenarios**:

1. **Given** a new query request, **When** the request is processed, **Then** the system returns a session ID in the initial response message.
2. **Given** an existing session ID, **When** the user sends a resume request with a new prompt, **Then** the system continues the conversation with full previous context.
3. **Given** a session ID, **When** the user requests to fork the session, **Then** the system creates a new session branch preserving the original.

---

### User Story 3 - Tool Configuration (Priority: P1)

A developer wants to control which tools the agent can use, restricting or allowing specific capabilities based on their application's needs.

**Why this priority**: Tool control is fundamental to security and application design. Developers MUST be able to limit agent capabilities to prevent unintended actions.

**Independent Test**: Can be tested by configuring allowed tools and verifying the agent only uses permitted tools.

**Acceptance Scenarios**:

1. **Given** a list of allowed tools in the request, **When** the agent attempts to use an unlisted tool, **Then** the system blocks the tool use.
2. **Given** read-only tools configured, **When** the agent is asked to modify a file, **Then** the agent reports it cannot perform the action.
3. **Given** all built-in tools allowed, **When** the agent needs multiple tools, **Then** the system permits use of Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Task, NotebookEdit, and MultiEdit tools.

---

### User Story 4 - Custom Subagent Definition (Priority: P2)

A developer wants to define specialized subagents that the main agent can delegate tasks to, each with their own instructions and tool access.

**Why this priority**: Subagents enable modular, focused task execution and are essential for complex workflows requiring specialized expertise. They provide context isolation, parallelization, and specialized instructions.

**Independent Test**: Can be tested by defining a subagent programmatically or via filesystem and sending a prompt that explicitly invokes it by name.

**Acceptance Scenarios**:

1. **Given** a subagent definition with description and prompt, **When** the main agent determines the task matches the description, **Then** the system automatically spawns the subagent to handle the task.
2. **Given** a subagent with restricted tools, **When** the subagent executes, **Then** it can only use its configured tools (and cannot spawn nested subagents).
3. **Given** multiple subagents defined, **When** tasks arrive, **Then** the main agent can delegate to appropriate subagents based on their descriptions.
4. **Given** an explicit prompt mentioning a subagent by name (e.g., "Use the code-reviewer agent"), **When** the request is processed, **Then** the named subagent is directly invoked.
5. **Given** Task tool is in allowedTools without custom agents defined, **When** delegation is needed, **Then** the built-in general-purpose subagent is available.
6. **Given** a subagent is executing, **When** messages are streamed, **Then** messages from subagent context include parent_tool_use_id field.

---

### User Story 5 - MCP Server Integration (Priority: P2)

A developer wants to extend agent capabilities by connecting external MCP (Model Context Protocol) servers that provide additional tools and resources.

**Why this priority**: MCP servers enable extensibility - connecting to databases, browsers, APIs, and custom tools. This is critical for enterprise integrations.

**Independent Test**: Can be tested by configuring an MCP server and verifying the agent can use tools provided by that server.

**Acceptance Scenarios**:

1. **Given** an MCP server configuration with command and args, **When** a query starts, **Then** the system launches and connects to the MCP server via stdio transport.
2. **Given** an MCP server providing custom tools, **When** the agent needs those capabilities, **Then** the agent can invoke MCP tools using the mcp__server__action naming pattern.
3. **Given** an SSE-based MCP server URL and optional headers, **When** configured with type "sse", **Then** the system connects via SSE transport.
4. **Given** an HTTP-based MCP server URL and optional headers, **When** configured with type "http", **Then** the system connects via HTTP transport.
5. **Given** an MCP server configuration with environment variables using `${VAR:-default}` syntax, **When** the server starts, **Then** environment variables are resolved with fallback defaults.
6. **Given** an MCP server that exposes resources, **When** the agent queries resources, **Then** the agent can use mcp__list_resources and mcp__read_resource tools.
7. **Given** an MCP server fails to connect, **When** the query starts, **Then** the system init message includes the server status as "failed" in the mcp_servers array.

---

### User Story 6 - Permission Control (Priority: P2)

A developer wants fine-grained control over what the agent can do, including approval workflows for sensitive operations.

**Why this priority**: Permission control is essential for production deployments where uncontrolled agent actions could cause damage.

**Independent Test**: Can be tested by setting permission mode and verifying tool approval behavior matches expectations.

**Acceptance Scenarios**:

1. **Given** permission mode set to "acceptEdits", **When** the agent tries to edit files, **Then** edits are automatically approved.
2. **Given** permission mode set to "bypassPermissions", **When** the agent uses any tool, **Then** all tools execute without approval prompts.
3. **Given** default permission mode, **When** the agent requests to use a tool, **Then** the system invokes the permission callback for approval.

---

### User Story 7 - Hooks for Agent Lifecycle (Priority: P2)

A developer wants to intercept agent execution at key points to add custom validation, logging, or transformation logic.

**Why this priority**: Hooks enable custom business logic integration - audit logging, security validation, input/output transformation.

**Independent Test**: Can be tested by registering a PreToolUse hook and verifying it executes before tool calls.

**Acceptance Scenarios**:

1. **Given** a PreToolUse hook registered for "Bash", **When** the agent attempts a Bash command, **Then** the hook executes before the command runs.
2. **Given** a hook that returns deny, **When** the tool use is requested, **Then** the system blocks the operation.
3. **Given** a PostToolUse hook, **When** a tool completes, **Then** the hook receives the tool result for logging or transformation.

---

### User Story 8 - Structured Output (Priority: P3)

A developer wants the agent to return data in a specific JSON schema format for easy integration with their application.

**Why this priority**: Structured outputs enable type-safe integration but require the core query functionality to work first.

**Independent Test**: Can be tested by providing a JSON schema and verifying the agent's final output validates against it.

**Acceptance Scenarios**:

1. **Given** a JSON schema in the request, **When** the agent completes its task, **Then** the final result conforms to the schema.
2. **Given** an invalid schema, **When** the request is made, **Then** the system returns a schema validation error.
3. **Given** the agent cannot produce valid output, **When** retries are exhausted, **Then** the system returns a structured output error.

---

### User Story 9 - File Checkpointing and Rewind (Priority: P3)

A developer wants to track file changes made by the agent and revert to previous states if needed.

**Why this priority**: Checkpointing provides safety for file operations but is an advanced feature built on top of session management.

**Independent Test**: Can be tested by enabling checkpointing, having the agent modify files, then rewinding and verifying restoration.

**Acceptance Scenarios**:

1. **Given** file checkpointing enabled, **When** the agent modifies files via Write/Edit tools, **Then** the system tracks changes with checkpoint UUIDs.
2. **Given** a checkpoint UUID, **When** a rewind request is made, **Then** the system restores files to their state at that checkpoint.
3. **Given** a session with multiple checkpoints, **When** listing checkpoints, **Then** all checkpoint UUIDs and timestamps are returned.

---

### User Story 10 - Model Selection (Priority: P3)

A developer wants to choose which Claude model powers the agent, balancing cost, speed, and capability.

**Why this priority**: Model selection is important for optimization but the API works with any supported model.

**Independent Test**: Can be tested by specifying different models and verifying responses come from the requested model.

**Acceptance Scenarios**:

1. **Given** model "claude-sonnet-4-5" specified, **When** a query executes, **Then** the system uses Sonnet for that query.
2. **Given** model "haiku" specified for a subagent, **When** the subagent executes, **Then** it uses Haiku while the main agent uses its configured model.
3. **Given** no model specified, **When** a query executes, **Then** the system uses the default model.

---

### Edge Cases

- What happens when a session ID does not exist or has expired? → System returns HTTP 404 with error code SESSION_NOT_FOUND for non-existent sessions, or SESSION_EXPIRED for expired sessions with the expiration timestamp.
- How does the system handle MCP server connection failures? → System includes failed server status in mcp_servers array of init message; agent continues with available tools.
- What happens when the agent exceeds maximum turns without completing? → System terminates the agent gracefully and returns a result message with is_complete=false, stop_reason='max_turns_reached', and includes partial results.
- How does the system handle concurrent requests to the same session? → System uses optimistic locking. Second request receives HTTP 409 Conflict with error code SESSION_LOCKED and a retry-after header suggesting wait time.
- What happens when a hook callback times out? → Hook callbacks have a 30-second default timeout. On timeout, system treats hook as returning 'allow' and logs a warning. Timeout is configurable per hook.
- How does the system handle partial file writes during checkpointing? → File writes are atomic using write-to-temp-then-rename pattern. Partial writes are never checkpointed; only complete successful writes are recorded.
- What happens when tool execution times out? → Tools have type-specific timeouts (Bash: 2min, WebFetch: 30s, others: 60s). On timeout, tool returns error result and agent can retry or proceed.
- What happens when an MCP environment variable (e.g., `${API_TOKEN}`) is not set and has no default? → System fails MCP server initialization with clear error in mcp_servers status array (status='failed', error='Missing required environment variable: VAR_NAME'). Agent continues with other available tools.
- How does the system handle SSE/HTTP MCP server authentication failures (invalid headers/tokens)? → System reports auth failure in mcp_servers status (status='failed', error='Authentication failed: 401/403'). Agent continues without that server's tools.

## Requirements *(mandatory)*

### Functional Requirements

#### Core Agent Operations

- **FR-001**: System MUST accept prompts and stream agent responses in real-time
- **FR-002**: System MUST execute built-in tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Task, NotebookEdit, MultiEdit
- **FR-003**: System MUST support configuring allowed tools per request
- **FR-004**: System MUST stream messages as they occur (assistant messages, tool uses, tool results, system messages)
- **FR-005**: System MUST return a final result message when agent completes
- **FR-005a**: System MUST support streaming input mode with AsyncGenerator for real-time message queueing, image uploads, and interruption handling
- **FR-005b**: System MUST support single message mode for one-shot queries suitable for stateless/serverless environments

#### Session Management

- **FR-006**: System MUST generate and return session IDs for new queries
- **FR-007**: System MUST support resuming sessions using session ID
- **FR-008**: System MUST support forking sessions to create branches
- **FR-009**: System MUST maintain conversation context across resumed sessions

#### Tool and Agent Configuration

- **FR-010**: System MUST support defining custom subagents via three methods:
  - **FR-010a**: Programmatic definition via `agents` parameter with AgentDefinition (description, prompt, tools, model)
  - **FR-010b**: Filesystem-based definition via markdown files in .claude/agents/ directories
  - **FR-010c**: Built-in general-purpose subagent available when Task tool is in allowedTools
- **FR-010d**: System MUST require Task tool in allowedTools for subagent invocation
- **FR-010e**: System MUST support automatic subagent invocation based on description matching
- **FR-010f**: System MUST support explicit subagent invocation by name in prompt
- **FR-010g**: System MUST include parent_tool_use_id in messages from subagent context
- **FR-010h**: System MUST prevent subagents from spawning nested subagents (no Task in subagent tools)
- **FR-011**: System MUST support MCP server configuration with three transport types:
  - **FR-011a**: stdio transport - external processes communicating via stdin/stdout (command, args, env)
  - **FR-011b**: SSE transport - remote servers with Server-Sent Events (type: "sse", url, headers)
  - **FR-011c**: HTTP transport - remote servers with HTTP communication (type: "http", url, headers)
- **FR-011d**: System MUST support environment variable syntax `${VAR:-default}` in MCP server configuration
- **FR-011e**: System MUST include MCP server connection status in system init messages (mcp_servers array with status field)
- **FR-012**: System MUST support the mcp__server__action tool naming convention for MCP tools
- **FR-012a**: System MUST support mcp__list_resources and mcp__read_resource tools for MCP resource management
- **FR-013**: System MUST allow subagent model override (sonnet, opus, haiku, inherit)

#### Permission System

- **FR-014**: System MUST support permission modes: default (invokes canUseTool callback for each tool use requiring explicit approval), acceptEdits (auto-approve file modifications), bypassPermissions (skip all permission checks)
- **FR-015**: System MUST support dynamic permission mode changes during streaming
- **FR-016**: System MUST support custom permission callbacks (canUseTool)
- **FR-017**: System MUST handle AskUserQuestion tool for agent clarifications by streaming a special 'question' event type containing the question text, options (if any), and a question_id. Client responds via POST /sessions/{id}/answer with the question_id and answer text.

#### Hooks

- **FR-018**: System MUST support PreToolUse hooks with tool name matchers
- **FR-019**: System MUST support PostToolUse hooks for result interception
- **FR-020**: System MUST support hook responses: allow, deny, ask, with optional input transformation
- **FR-021**: System MUST support SubagentStop hooks for tracking subagent completion
- **FR-022**: System MUST support Stop hooks for agent completion events
- **FR-023**: System MUST support UserPromptSubmit hooks for prompt interception

#### Structured Output

- **FR-024**: System MUST support JSON schema output format specification
- **FR-025**: System MUST validate agent output against provided schema
- **FR-026**: System MUST return structured_output field in result messages

#### File Checkpointing

- **FR-027**: System MUST support enabling/disabling file checkpointing per request
- **FR-028**: System MUST track file changes from Write, Edit, NotebookEdit tools
- **FR-029**: System MUST return checkpoint UUIDs in user messages
- **FR-030**: System MUST support file rewind to any checkpoint

#### Configuration

- **FR-031**: System MUST support working directory configuration (cwd)
- **FR-032**: System MUST support environment variable injection
- **FR-033**: System MUST support max_turns limit configuration. When limit is reached, agent terminates gracefully with stop_reason='max_turns_reached' in result message.
- **FR-034**: System MUST support system prompt customization via four methods:
  - **FR-034a**: CLAUDE.md files loaded via settingSources (project-level and user-level)
  - **FR-034b**: Output styles from .claude/output-styles/ directories
  - **FR-034c**: Preset with append (claude_code preset + custom append string)
  - **FR-034d**: Custom system prompt strings (complete replacement)
- **FR-035**: System MUST support setting sources configuration (project, user)

#### Cost Tracking & Usage

- **FR-036**: System MUST include usage data (input_tokens, output_tokens, cache_read_input_tokens) in streamed assistant messages
- **FR-037**: System MUST include cumulative total_cost_usd in result messages
- **FR-038**: System MUST include per-model usage breakdown (modelUsage) in result messages when multiple models are used

#### Plugins

- **FR-039**: System MUST support loading plugins from local filesystem paths
- **FR-040**: System MUST support multiple plugins from different locations
- **FR-041**: System MUST expose loaded plugins in system init messages
- **FR-042**: System MUST namespace plugin commands as plugin-name:command-name

#### Skills

- **FR-043**: System MUST load skills from filesystem when settingSources includes "project" or "user"
- **FR-044**: System MUST enable skill invocation when "Skill" is in allowedTools
- **FR-045**: System MUST support skill discovery (listing available skills)
- **FR-046**: System MUST support project skills (.claude/skills/) and user skills (~/.claude/skills/)

#### Slash Commands

- **FR-047**: System MUST discover slash commands from .claude/commands/ directories
- **FR-048**: System MUST expose available slash commands in system init messages
- **FR-049**: System MUST support sending slash commands via prompt string (e.g., "/compact", "/clear")
- **FR-050**: System MUST support custom slash command arguments and placeholders ($1, $2, $ARGUMENTS)

#### TODO List Tracking

- **FR-051**: System MUST stream TodoWrite tool use messages when agent creates/updates todos
- **FR-052**: System MUST include full todo data in tool use messages (content, status, activeForm)
- **FR-053**: System MUST support todo statuses: pending, in_progress, completed

### Key Entities

- **Query**: A request to the agent containing prompt, options, and configuration
- **Session**: A persistent conversation context identified by session ID
- **Message**: A streamed response unit (system, user, assistant, result types)
- **Tool**: A capability the agent can invoke (built-in or MCP-provided)
- **Subagent**: A specialized agent definition with its own prompt and tool access
- **Hook**: An interception point for custom logic during agent execution
- **Checkpoint**: A saved file state identified by UUID for potential rewind
- **MCP Server**: An external tool provider connected via Model Context Protocol
- **Plugin**: A bundled package of commands, agents, skills, hooks, and MCP servers loaded from filesystem
- **Skill**: A SKILL.md file that Claude autonomously invokes based on context
- **Slash Command**: A user-invoked /command defined as markdown in .claude/commands/
- **Usage**: Token consumption data for billing (input_tokens, output_tokens, cache tokens, cost)
- **Todo**: A task item with content, status (pending/in_progress/completed), and activeForm for progress tracking

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can send a prompt and receive streamed agent responses within 2 seconds of first token
- **SC-002**: Sessions can be resumed with full context after any duration (limited by session storage)
- **SC-003**: Custom subagents execute tasks using only their permitted tools 100% of the time
- **SC-004**: MCP servers connect successfully and provide tools to agents within 5 seconds
- **SC-005**: Hooks execute for 100% of matching tool calls with no missed events
- **SC-006**: Structured outputs validate against provided schemas with zero invalid responses
- **SC-007**: File rewind restores files to exact checkpoint state with no data loss
- **SC-008**: Permission modes correctly govern tool approval for all tool types
- **SC-009**: API handles 100 concurrent agent sessions maintaining p95 latency under 500ms and error rate below 1%
- **SC-010**: All SDK features accessible via HTTP API with feature parity

## Clarifications

### Session 2026-01-06

- Q: Should the API support both streaming input mode (AsyncGenerator for real-time message queueing, image uploads, interruptions) and single message mode (one-shot queries for stateless environments)? → A: Support both streaming input and single message modes as distinct API patterns
- Q: How should token usage and cost data be exposed? → A: Full usage data in streamed messages AND cumulative totals (including total_cost_usd, modelUsage) in result messages
- Q: Should the API support plugins, skills, and slash commands extensibility? → A: Support all three via filesystem paths in API configuration (plugins loaded via paths, skills via settingSources + Skill tool, slash commands via filesystem directories)
- Q: How should TODO list tracking be exposed? → A: Stream TodoWrite tool use messages with full todo data (content, status, activeForm) for real-time progress tracking
- Q: How should system prompt modification be supported? → A: Support all four methods: CLAUDE.md files (via settingSources), output styles (.claude/output-styles/), preset+append (claude_code preset with custom append), and custom system prompt strings

### Session 2026-01-07

- Q: How should subagents be defined and invoked? → A: Support three methods: programmatic (agents parameter with AgentDefinition), filesystem-based (.claude/agents/ markdown files), and built-in general-purpose. Require Task tool in allowedTools, support automatic invocation via description matching, explicit invocation by name, and include parent_tool_use_id in subagent context messages. Subagents cannot spawn nested subagents.
- Q: What MCP transport types and features should be supported? → A: Three transports: stdio (command/args/env), SSE (url/headers), HTTP (url/headers). Support `${VAR:-default}` environment variable syntax, mcp_servers status array in init messages, and mcp__list_resources/mcp__read_resource for resource management (per official SDK docs).

## Assumptions

- The Claude Agent SDK (claude-agent-sdk Python package) is available and installed
- Valid Anthropic API credentials are configured via environment variables
- File system access is available for agent tool operations
- MCP servers are compatible with stdio, SSE, or HTTP transports per SDK specification
- MCP servers expose tools via the Model Context Protocol standard
- Clients support Server-Sent Events (SSE) for streaming responses

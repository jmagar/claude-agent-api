# Claude Agent API - Complete Endpoint Reference

**Version:** 0.1.0
**Base URL:** `http://localhost:54000`

---

## Table of Contents

- [Authentication](#authentication)
- [Root Endpoints](#root-endpoints)
- [Native API (`/api/v1/*`)](#native-api-apiv1)
  - [Projects](#projects)
  - [Agents](#agents)
  - [Query & Interaction](#query--interaction)
  - [Sessions](#sessions)
  - [Session Control](#session-control)
  - [Checkpoints](#checkpoints)
  - [Skills](#skills)
  - [Slash Commands](#slash-commands)
  - [MCP Servers](#mcp-servers)
  - [Memories](#memories-mem0)
  - [Tool Presets](#tool-presets)
- [OpenAI-Compatible API (`/v1/*`)](#openai-compatible-api-v1)
  - [Chat Completions](#chat-completions)
  - [Models](#models)
  - [Assistants (Beta)](#assistants-beta)
  - [Threads (Beta)](#threads-beta)
  - [Messages (Beta)](#messages-beta)
  - [Runs (Beta)](#runs-beta)
- [Response Formats](#response-formats)
- [Notes & Features](#notes--features)

---

## Authentication

### Native Endpoints (`/api/v1/*`)

All native endpoints require authentication via the `X-API-Key` header:

```http
X-API-Key: your-api-key-here
```

### OpenAI Endpoints (`/v1/*`)

OpenAI-compatible endpoints support Bearer token authentication:

```http
Authorization: Bearer your-api-key-here
```

**Exception:** Health and root endpoints do not require authentication.

---

## Root Endpoints

### Get Service Info

```http
GET /
```

**Response:**
```json
{
  "service": "claude-agent-api",
  "version": "0.1.0"
}
```

### Health Check

```http
GET /health
GET /api/v1/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "dependencies": {
    "postgres": {
      "status": "ok",
      "latency_ms": 2.5
    },
    "redis": {
      "status": "ok",
      "latency_ms": 1.2
    }
  }
}
```

**Status Values:**
- `ok`: All dependencies healthy
- `degraded`: Some dependencies unhealthy
- `unhealthy`: All dependencies unhealthy

---

## Native API (`/api/v1/*`)

### Projects

#### List Projects

```http
GET /api/v1/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": "uuid",
      "name": "My Project",
      "path": "/path/to/project",
      "metadata": {},
      "created_at": "2026-02-10T12:00:00Z",
      "updated_at": "2026-02-10T12:00:00Z"
    }
  ],
  "total": 1
}
```

#### Create Project

```http
POST /api/v1/projects
Content-Type: application/json

{
  "name": "My Project",
  "path": "/path/to/project",
  "metadata": {}
}
```

**Status:** `201 Created`

#### Get Project

```http
GET /api/v1/projects/{project_id}
```

#### Update Project

```http
PATCH /api/v1/projects/{project_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "metadata": {}
}
```

#### Delete Project

```http
DELETE /api/v1/projects/{project_id}
```

**Status:** `204 No Content`

---

### Agents

#### List Agents

```http
GET /api/v1/agents
```

**Response:**
```json
{
  "agents": [
    {
      "id": "uuid",
      "name": "Code Assistant",
      "description": "Helps with coding tasks",
      "prompt": "You are a helpful coding assistant...",
      "tools": ["Bash", "Edit", "Read"],
      "model": "sonnet",
      "created_at": "2026-02-10T12:00:00Z"
    }
  ]
}
```

#### Create Agent

```http
POST /api/v1/agents
Content-Type: application/json

{
  "name": "Code Assistant",
  "description": "Helps with coding tasks",
  "prompt": "You are a helpful coding assistant...",
  "tools": ["Bash", "Edit", "Read"],
  "model": "sonnet"
}
```

**Status:** `201 Created`

#### Get Agent

```http
GET /api/v1/agents/{agent_id}
```

#### Update Agent

```http
PUT /api/v1/agents/{agent_id}
Content-Type: application/json

{
  "name": "Updated Agent",
  "description": "Updated description",
  "prompt": "Updated prompt...",
  "tools": ["Bash", "Edit"],
  "model": "haiku"
}
```

#### Delete Agent

```http
DELETE /api/v1/agents/{agent_id}
```

**Status:** `204 No Content`

#### Share Agent

```http
POST /api/v1/agents/{agent_id}/share
```

**Response:**
```json
{
  "share_url": "http://localhost:54000/share/agents/{agent_id}",
  "share_token": "abc123def456"
}
```

---

### Query & Interaction

#### Streaming Query (SSE)

```http
POST /api/v1/query
Content-Type: application/json

{
  "prompt": "Hello, Claude!",
  "session_id": "uuid (optional)",
  "model": "sonnet",
  "max_turns": 10,
  "permission_mode": "bypassPermissions",
  "include_partial_messages": true,
  "allowed_tools": [],
  "disallowed_tools": [],
  "mcp_servers": {}
}
```

**Response:** Server-Sent Events (SSE) stream

**Event Types:**
- `init`: Session initialization
- `message`: Agent messages (user, assistant, system)
- `question`: Agent asking for user input
- `partial`: Content deltas (if enabled)
- `result`: Final result with stats
- `error`: Error events
- `done`: Stream completion

#### Non-Streaming Query

```http
POST /api/v1/query/single
Content-Type: application/json

{
  "prompt": "Hello, Claude!",
  "session_id": "uuid (optional)",
  "model": "sonnet"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "content": "Hello! How can I help you?",
  "model": "sonnet",
  "num_turns": 1,
  "is_error": false,
  "stop_reason": "completed",
  "total_cost_usd": 0.02
}
```

#### WebSocket Query

```http
WS /api/v1/query/ws
X-API-Key: your-api-key-here
```

**Client → Server Messages:**

```json
{
  "type": "prompt",
  "prompt": "Hello!",
  "model": "sonnet"
}
```

```json
{
  "type": "interrupt",
  "session_id": "uuid"
}
```

```json
{
  "type": "answer",
  "session_id": "uuid",
  "answer": "Yes, proceed"
}
```

```json
{
  "type": "control",
  "session_id": "uuid",
  "permission_mode": "default"
}
```

**Server → Client Messages:**

```json
{
  "type": "sse_event",
  "event": "message",
  "data": {}
}
```

```json
{
  "type": "ack",
  "message": "Query started"
}
```

```json
{
  "type": "error",
  "message": "Error description"
}
```

---

### Sessions

#### List Sessions

```http
GET /api/v1/sessions?mode=code&project_id=uuid&tags=tag1,tag2&search=query&page=1&page_size=50
```

**Query Parameters:**
- `mode` (optional): Filter by mode
- `project_id` (optional): Filter by project
- `tags` (optional): Filter by tags (comma-separated)
- `search` (optional): Search query
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 100): Items per page

**Response:**
```json
{
  "sessions": [
    {
      "id": "uuid",
      "status": "completed",
      "model": "sonnet",
      "created_at": "2026-02-10T12:00:00Z",
      "updated_at": "2026-02-10T12:05:00Z",
      "total_turns": 5,
      "total_cost_usd": 0.10,
      "parent_session_id": null,
      "mode": "code",
      "project_id": "uuid",
      "tags": ["feature", "bugfix"]
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

#### Get Session

```http
GET /api/v1/sessions/{session_id}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "model": "sonnet",
  "created_at": "2026-02-10T12:00:00Z",
  "updated_at": "2026-02-10T12:05:00Z",
  "total_turns": 5,
  "total_cost_usd": 0.10,
  "parent_session_id": null
}
```

#### Promote Session

```http
POST /api/v1/sessions/{session_id}/promote
Content-Type: application/json

{
  "project_id": "uuid"
}
```

**Description:** Promotes a brainstorm session to code mode.

#### Update Session Tags

```http
PATCH /api/v1/sessions/{session_id}/tags
Content-Type: application/json

{
  "tags": ["feature", "bugfix", "urgent"]
}
```

---

### Session Control

#### Resume Session

```http
POST /api/v1/sessions/{session_id}/resume
Content-Type: application/json

{
  "prompt": "Continue with...",
  "images": [],
  "allowed_tools": [],
  "disallowed_tools": [],
  "permission_mode": "bypassPermissions",
  "max_turns": 10,
  "hooks": null
}
```

**Response:** SSE stream (same as `/api/v1/query`)

#### Fork Session

```http
POST /api/v1/sessions/{session_id}/fork
Content-Type: application/json

{
  "prompt": "Try a different approach...",
  "model": "sonnet",
  "allowed_tools": [],
  "disallowed_tools": [],
  "permission_mode": "bypassPermissions",
  "max_turns": 10,
  "hooks": null
}
```

**Response:** SSE stream with new session ID

**Description:** Creates a new session inheriting parent's history.

#### Interrupt Session

```http
POST /api/v1/sessions/{session_id}/interrupt
```

**Response:**
```json
{
  "status": "interrupted",
  "session_id": "uuid"
}
```

#### Send Control Event

```http
POST /api/v1/sessions/{session_id}/control
Content-Type: application/json

{
  "type": "permission_mode_change",
  "permission_mode": "default"
}
```

**Response:**
```json
{
  "status": "accepted",
  "session_id": "uuid",
  "permission_mode": "default"
}
```

**Permission Modes:**
- `default`: Prompt for tool usage
- `acceptEdits`: Auto-approve file edits
- `plan`: Require plan approval
- `bypassPermissions`: Auto-approve all tools

#### Answer Question

```http
POST /api/v1/sessions/{session_id}/answer
Content-Type: application/json

{
  "answer": "Yes, proceed with the changes"
}
```

**Response:**
```json
{
  "status": "accepted",
  "session_id": "uuid"
}
```

---

### Checkpoints

#### List Checkpoints

```http
GET /api/v1/sessions/{session_id}/checkpoints
```

**Response:**
```json
{
  "checkpoints": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "user_message_uuid": "uuid",
      "created_at": "2026-02-10T12:00:00Z",
      "files_modified": 5
    }
  ]
}
```

#### Rewind to Checkpoint

```http
POST /api/v1/sessions/{session_id}/rewind
Content-Type: application/json

{
  "checkpoint_id": "uuid"
}
```

**Response:**
```json
{
  "status": "validated",
  "checkpoint_id": "uuid",
  "message": "Checkpoint validated. File restoration pending SDK support."
}
```

---

### Skills

#### List Skills

```http
GET /api/v1/skills?source=filesystem
```

**Query Parameters:**
- `source` (optional): `filesystem`, `database`, or omit for both

**Response:**
```json
{
  "skills": [
    {
      "id": "fs:my-skill",
      "name": "my-skill",
      "description": "Skill description",
      "content": "Skill content...",
      "enabled": true,
      "source": "filesystem",
      "path": "/path/to/skill.md"
    },
    {
      "id": "uuid",
      "name": "db-skill",
      "description": "Database skill",
      "content": "Skill content...",
      "enabled": true,
      "source": "database",
      "created_at": "2026-02-10T12:00:00Z",
      "updated_at": "2026-02-10T12:00:00Z"
    }
  ]
}
```

#### Create Skill

```http
POST /api/v1/skills
Content-Type: application/json

{
  "name": "my-skill",
  "description": "Skill description",
  "content": "Skill content...",
  "enabled": true
}
```

**Status:** `201 Created`

**Note:** Creates in database. For filesystem skills, create `.md` files in `.claude/skills/`.

#### Get Skill

```http
GET /api/v1/skills/{skill_id}
```

**Skill ID Format:**
- Filesystem: `fs:skill-name`
- Database: `uuid`

#### Update Skill

```http
PUT /api/v1/skills/{skill_id}
Content-Type: application/json

{
  "name": "updated-skill",
  "description": "Updated description",
  "content": "Updated content...",
  "enabled": false
}
```

**Note:** Only database skills can be updated via API.

#### Delete Skill

```http
DELETE /api/v1/skills/{skill_id}
```

**Status:** `204 No Content`

**Note:** Only database skills can be deleted via API.

---

### Slash Commands

#### List Slash Commands

```http
GET /api/v1/slash-commands
```

**Response:**
```json
{
  "commands": [
    {
      "id": "uuid",
      "name": "my-command",
      "description": "Command description",
      "content": "Command prompt...",
      "enabled": true,
      "created_at": "2026-02-10T12:00:00Z"
    }
  ]
}
```

#### Create Slash Command

```http
POST /api/v1/slash-commands
Content-Type: application/json

{
  "name": "my-command",
  "description": "Command description",
  "content": "Command prompt...",
  "enabled": true
}
```

**Status:** `201 Created`

#### Get Slash Command

```http
GET /api/v1/slash-commands/{command_id}
```

#### Update Slash Command

```http
PUT /api/v1/slash-commands/{command_id}
Content-Type: application/json

{
  "name": "updated-command",
  "description": "Updated description",
  "content": "Updated prompt...",
  "enabled": false
}
```

#### Delete Slash Command

```http
DELETE /api/v1/slash-commands/{command_id}
```

**Status:** `204 No Content`

---

### MCP Servers

#### List MCP Servers

```http
GET /api/v1/mcp-servers?source=database
```

**Query Parameters:**
- `source` (optional): `filesystem`, `database`, or omit for both

**Response:**
```json
{
  "servers": [
    {
      "id": "fs:github",
      "name": "github",
      "transport_type": "stdio",
      "command": "mcp-github",
      "args": ["--repo", "myorg/myrepo"],
      "url": null,
      "headers": {},
      "env": {
        "GITHUB_TOKEN": "***REDACTED***"
      },
      "enabled": true,
      "status": "active",
      "source": "filesystem"
    }
  ]
}
```

**Note:** Filesystem server credentials are redacted for security.

#### Create MCP Server

```http
POST /api/v1/mcp-servers
Content-Type: application/json

{
  "name": "my-server",
  "type": "stdio",
  "config": {
    "command": "python",
    "args": ["server.py"],
    "env": {
      "API_KEY": "secret"
    }
  }
}
```

**Status:** `201 Created`

**Transport Types:**
- `stdio`: Standard input/output
- `sse`: Server-Sent Events

#### Get MCP Server

```http
GET /api/v1/mcp-servers/{name}
```

**Server Name Format:**
- Filesystem: `fs:server-name`
- Database: `server-name`

#### Update MCP Server

```http
PUT /api/v1/mcp-servers/{name}
Content-Type: application/json

{
  "type": "stdio",
  "config": {
    "command": "python",
    "args": ["server.py"],
    "enabled": false
  }
}
```

**Note:** Only database servers can be updated via API.

#### Delete MCP Server

```http
DELETE /api/v1/mcp-servers/{name}
```

**Status:** `204 No Content`

**Note:** Only database servers can be deleted via API.

#### List MCP Resources

```http
GET /api/v1/mcp-servers/{name}/resources
```

**Response:**
```json
{
  "resources": [
    {
      "uri": "resource://path",
      "name": "Resource Name",
      "description": "Resource description",
      "mimeType": "text/plain"
    }
  ]
}
```

#### Get MCP Resource

```http
GET /api/v1/mcp-servers/{name}/resources/{uri:path}
```

**Response:**
```json
{
  "uri": "resource://path",
  "mimeType": "text/plain",
  "text": "Resource content..."
}
```

#### Create MCP Share

```http
POST /api/v1/mcp-servers/{name}/share
Content-Type: application/json

{
  "config": {
    "type": "stdio",
    "command": "python",
    "args": ["server.py"]
  }
}
```

**Response:**
```json
{
  "share_token": "abc123def456",
  "name": "my-server",
  "config": {
    "type": "stdio",
    "command": "python",
    "args": ["server.py"],
    "env": {
      "API_KEY": "***REDACTED***"
    }
  },
  "created_at": "2026-02-10T12:00:00Z"
}
```

#### Resolve MCP Share

```http
GET /api/v1/mcp-servers/share/{token}
```

**Response:**
```json
{
  "name": "my-server",
  "config": {
    "type": "stdio",
    "command": "python",
    "args": ["server.py"]
  },
  "created_at": "2026-02-10T12:00:00Z"
}
```

---

### Memories (Mem0)

#### Search Memories

```http
POST /api/v1/memories/search
Content-Type: application/json

{
  "query": "What are my preferences?",
  "limit": 10,
  "enable_graph": true
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "memory": "User prefers technical explanations",
      "score": 0.95,
      "metadata": {
        "category": "preferences"
      }
    }
  ],
  "count": 1
}
```

#### Add Memory

```http
POST /api/v1/memories
Content-Type: application/json

{
  "messages": "User prefers concise responses",
  "metadata": {
    "category": "preferences"
  },
  "enable_graph": true
}
```

**Status:** `201 Created`

**Response:**
```json
{
  "memories": [
    {
      "id": "uuid",
      "memory": "User prefers concise responses",
      "hash": "abc123",
      "created_at": "2026-02-10T12:00:00Z",
      "user_id": "hashed-api-key"
    }
  ],
  "count": 1
}
```

#### List Memories

```http
GET /api/v1/memories
```

**Response:**
```json
{
  "memories": [
    {
      "id": "uuid",
      "memory": "User prefers technical explanations",
      "created_at": "2026-02-10T12:00:00Z"
    }
  ],
  "count": 1
}
```

#### Delete Memory

```http
DELETE /api/v1/memories/{memory_id}
```

**Response:**
```json
{
  "deleted": true,
  "message": "Memory {memory_id} deleted"
}
```

#### Delete All Memories

```http
DELETE /api/v1/memories
```

**Response:**
```json
{
  "deleted": true,
  "message": "All memories deleted"
}
```

---

### Tool Presets

#### List Tool Presets

```http
GET /api/v1/tool-presets
```

**Response:**
```json
{
  "presets": [
    {
      "id": "uuid",
      "name": "Read Only",
      "description": "Only read operations allowed",
      "allowed_tools": ["Read", "Glob", "Grep"],
      "disallowed_tools": ["Edit", "Write", "Bash"],
      "created_at": "2026-02-10T12:00:00Z"
    }
  ]
}
```

#### Create Tool Preset

```http
POST /api/v1/tool-presets
Content-Type: application/json

{
  "name": "Read Only",
  "description": "Only read operations allowed",
  "allowed_tools": ["Read", "Glob", "Grep"],
  "disallowed_tools": ["Edit", "Write", "Bash"]
}
```

**Status:** `201 Created`

#### Get Tool Preset

```http
GET /api/v1/tool-presets/{preset_id}
```

#### Update Tool Preset

```http
PUT /api/v1/tool-presets/{preset_id}
Content-Type: application/json

{
  "name": "Read Only Updated",
  "description": "Updated description",
  "allowed_tools": ["Read", "Glob"],
  "disallowed_tools": ["Edit", "Write", "Bash", "Task"]
}
```

#### Delete Tool Preset

```http
DELETE /api/v1/tool-presets/{preset_id}
```

**Status:** `204 No Content`

---

## OpenAI-Compatible API (`/v1/*`)

### Chat Completions

#### Create Chat Completion

```http
POST /v1/chat/completions
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Non-Streaming Response:**
```json
{
  "id": "chatcmpl-uuid",
  "object": "chat.completion",
  "created": 1707566400,
  "model": "sonnet",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

**Streaming Response (SSE):**

```
data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1707566400,"model":"sonnet","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1707566400,"model":"sonnet","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"chatcmpl-uuid","object":"chat.completion.chunk","created":1707566400,"model":"sonnet","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**Optional Headers:**
- `X-Permission-Mode`: Override permission mode (`default`, `acceptEdits`, `plan`, `bypassPermissions`)

**Model Mapping:**
- `gpt-4` → `sonnet`
- `gpt-4o` → `opus`
- `gpt-3.5-turbo` → `haiku`

**Limitations:**
- `temperature`, `top_p`, `max_tokens`, `stop` parameters are accepted but ignored (Claude Agent SDK does not support)
- Only text content blocks supported (no tool calls yet)
- Single completion only (`n` parameter not supported)
- No logprobs support

---

### Models

#### List Models

```http
GET /v1/models
Authorization: Bearer your-api-key-here
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1707566400,
      "owned_by": "anthropic"
    },
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1707566400,
      "owned_by": "anthropic"
    },
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1707566400,
      "owned_by": "anthropic"
    }
  ]
}
```

#### Get Model

```http
GET /v1/models/{model_id}
Authorization: Bearer your-api-key-here
```

**Response:**
```json
{
  "id": "gpt-4",
  "object": "model",
  "created": 1707566400,
  "owned_by": "anthropic"
}
```

---

### Assistants (Beta)

#### Create Assistant

```http
POST /v1/assistants
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "model": "gpt-4",
  "name": "Math Tutor",
  "description": "Helps with math problems",
  "instructions": "You are a helpful math tutor...",
  "tools": [{"type": "code_interpreter"}],
  "metadata": {}
}
```

**Status:** `201 Created`

#### List Assistants

```http
GET /v1/assistants?limit=20&order=desc
Authorization: Bearer your-api-key-here
```

**Query Parameters:**
- `limit` (1-100, default: 20)
- `order` (`asc` or `desc`, default: `desc`)
- `after` (cursor)
- `before` (cursor)

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "asst_uuid",
      "object": "assistant",
      "created_at": 1707566400,
      "model": "gpt-4",
      "name": "Math Tutor",
      "description": "Helps with math problems",
      "instructions": "You are a helpful math tutor...",
      "tools": [{"type": "code_interpreter"}],
      "metadata": {}
    }
  ],
  "first_id": "asst_uuid",
  "last_id": "asst_uuid",
  "has_more": false
}
```

#### Get Assistant

```http
GET /v1/assistants/{assistant_id}
Authorization: Bearer your-api-key-here
```

#### Modify Assistant

```http
POST /v1/assistants/{assistant_id}
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "name": "Updated Tutor",
  "instructions": "Updated instructions..."
}
```

#### Delete Assistant

```http
DELETE /v1/assistants/{assistant_id}
Authorization: Bearer your-api-key-here
```

**Response:**
```json
{
  "id": "asst_uuid",
  "object": "assistant.deleted",
  "deleted": true
}
```

---

### Threads (Beta)

#### Create Thread

```http
POST /v1/threads
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "content": "Hello!",
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

**Status:** `201 Created`

#### Get Thread

```http
GET /v1/threads/{thread_id}
Authorization: Bearer your-api-key-here
```

**Response:**
```json
{
  "id": "thread_uuid",
  "object": "thread",
  "created_at": 1707566400,
  "metadata": {}
}
```

#### Modify Thread

```http
POST /v1/threads/{thread_id}
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "metadata": {
    "key": "value"
  }
}
```

#### Delete Thread

```http
DELETE /v1/threads/{thread_id}
Authorization: Bearer your-api-key-here
```

**Response:**
```json
{
  "id": "thread_uuid",
  "object": "thread.deleted",
  "deleted": true
}
```

---

### Messages (Beta)

#### Create Message

```http
POST /v1/threads/{thread_id}/messages
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "role": "user",
  "content": "Hello!",
  "metadata": {}
}
```

**Status:** `201 Created`

#### List Messages

```http
GET /v1/threads/{thread_id}/messages?limit=20&order=desc
Authorization: Bearer your-api-key-here
```

**Query Parameters:**
- `limit` (1-100, default: 20)
- `order` (`asc` or `desc`, default: `desc`)
- `after` (cursor)
- `before` (cursor)

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "msg_uuid",
      "object": "thread.message",
      "created_at": 1707566400,
      "thread_id": "thread_uuid",
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": {
            "value": "Hello!"
          }
        }
      ],
      "metadata": {}
    }
  ],
  "first_id": "msg_uuid",
  "last_id": "msg_uuid",
  "has_more": false
}
```

#### Get Message

```http
GET /v1/threads/{thread_id}/messages/{message_id}
Authorization: Bearer your-api-key-here
```

#### Modify Message

```http
POST /v1/threads/{thread_id}/messages/{message_id}
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "metadata": {
    "key": "value"
  }
}
```

---

### Runs (Beta)

#### Create Run

```http
POST /v1/threads/{thread_id}/runs
Authorization: Bearer your-api-key-here
Content-Type: application/json

{
  "assistant_id": "asst_uuid",
  "model": "gpt-4",
  "instructions": "Optional override instructions",
  "tools": [],
  "metadata": {}
}
```

**Status:** `201 Created`

#### List Runs

```http
GET /v1/threads/{thread_id}/runs?limit=20&order=desc
Authorization: Bearer your-api-key-here
```

**Query Parameters:**
- `limit` (1-100, default: 20)
- `order` (`asc` or `desc`, default: `desc`)

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "run_uuid",
      "object": "thread.run",
      "created_at": 1707566400,
      "thread_id": "thread_uuid",
      "assistant_id": "asst_uuid",
      "status": "completed",
      "model": "gpt-4",
      "instructions": "Instructions...",
      "tools": [],
      "metadata": {}
    }
  ],
  "first_id": "run_uuid",
  "last_id": "run_uuid",
  "has_more": false
}
```

#### Get Run

```http
GET /v1/threads/{thread_id}/runs/{run_id}
Authorization: Bearer your-api-key-here
```

#### Cancel Run

```http
POST /v1/threads/{thread_id}/runs/{run_id}/cancel
Authorization: Bearer your-api-key-here
```

**Response:**
```json
{
  "id": "run_uuid",
  "object": "thread.run",
  "status": "cancelled",
  ...
}
```

---

## Response Formats

### Native API

All native endpoints return JSON responses with consistent error formats:

**Success Response:**
```json
{
  "field1": "value",
  "field2": 123
}
```

**Error Response:**
```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE",
    "status": 400
  }
}
```

### OpenAI API

OpenAI-compatible endpoints follow OpenAI's error format:

**Error Response:**
```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

**Error Type Mapping:**
- 400 → `invalid_request_error`
- 401 → `authentication_error`
- 404 → `not_found_error`
- 429 → `rate_limit_error`
- 500 → `server_error`

---

## Notes & Features

### Multi-Tenancy

All database resources (MCP servers, skills, slash commands, memories, etc.) are scoped to the authenticated API key. Users cannot access other tenants' data.

### Server-Side MCP Configuration

Three-tier MCP server configuration system:

1. **Application-Level** (`.mcp-server-config.json` in project root)
   - Global servers available to all API keys
   - Environment variable resolution: `${VAR_NAME}`

2. **API-Key-Level** (Redis database)
   - Per-tenant configurations
   - Complete isolation between API keys

3. **Request-Level** (`mcp_servers` field in request)
   - Highest precedence
   - Explicit opt-out with empty dict `{}`

**Precedence:** Application < API-Key < Request

### Filesystem Discovery

Skills and MCP servers support discovery from filesystem:

- **Skills:** `.claude/skills/*.md` (YAML frontmatter)
- **MCP Servers:** `~/.claude.json`, `.mcp.json`, `.claude/mcp.json`

Filesystem resources are read-only via API.

### Memory System (Mem0)

Multi-tenant persistent memory with:
- **Vector Search:** Qdrant (Qwen/Qwen3-Embedding-0.6B, 1024 dims)
- **Graph Storage:** Neo4j for entity relationships
- **Per-Request Toggle:** `enable_graph` parameter

### Graceful Shutdown

API waits up to 30 seconds for active sessions before shutdown:
- Active sessions reject new requests during shutdown
- In-progress queries complete normally

### Rate Limiting

Configured via middleware (see project `CLAUDE.md` for specifics).

### WebSocket Communication

Bidirectional real-time agent interaction:
- Send prompts, interrupts, answers, control events
- Receive SSE events as WebSocket messages
- Single persistent connection

### Session Management

- **Resume:** Continue existing session
- **Fork:** Create new session inheriting parent history
- **Interrupt:** Stop running query
- **Checkpoints:** Snapshot file states for rewinding

### Streaming

Both native and OpenAI endpoints support:
- **SSE (Server-Sent Events):** One-way streaming
- **WebSocket:** Bidirectional streaming

---

**For detailed implementation specs, see:**
- [Feature Spec](specs/001-claude-agent-api/spec.md)
- [OpenAPI Contract](specs/001-claude-agent-api/contracts/openapi.yaml)
- [Server-Side MCP Spec](specs/server-side-mcp/spec.md)

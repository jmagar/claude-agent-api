# Next.js BFF (Backend For Frontend) API Routes

**Feature Branch**: `002-claude-agent-web`
**Date**: 2026-01-10

## Overview

This document defines all Next.js API routes that serve as the Backend For Frontend (BFF) layer. These routes sit between the React frontend and the Claude Agent API backend, providing:

- **Request transformation**: Adapt frontend requests to backend API format
- **Response aggregation**: Combine multiple backend calls into single responses
- **Session management**: Handle session state and caching
- **Authentication**: Validate API keys and manage auth state
- **Error handling**: Transform backend errors into user-friendly messages

---

## Route Structure

```
app/api/
├── streaming/
│   └── route.ts              # POST - SSE streaming proxy to backend
├── sessions/
│   ├── route.ts              # GET, POST - List and create sessions
│   └── [id]/
│       ├── route.ts          # GET, PATCH, DELETE - Session details
│       ├── messages/
│       │   └── route.ts      # GET - Session messages
│       ├── resume/
│       │   └── route.ts      # POST - Resume session
│       ├── fork/
│       │   └── route.ts      # POST - Fork session
│       ├── tags/
│       │   └── route.ts      # PATCH - Update tags
│       ├── promote/
│       │   └── route.ts      # POST - Promote to Code mode
│       └── checkpoints/
│           └── route.ts      # GET - List checkpoints
├── projects/
│   ├── route.ts              # GET, POST - List and create projects
│   └── [id]/
│       └── route.ts          # GET, PATCH, DELETE - Project details
├── agents/
│   ├── route.ts              # GET, POST - List and create agents
│   └── [id]/
│       ├── route.ts          # GET, PUT, DELETE - Agent details
│       └── share/
│           └── route.ts      # POST - Generate share link
├── skills/
│   ├── route.ts              # GET, POST - List and create skills
│   └── [id]/
│       ├── route.ts          # GET, PUT, DELETE - Skill details
│       └── share/
│           └── route.ts      # POST - Generate share link
├── slash-commands/
│   ├── route.ts              # GET, POST - List and create commands
│   └── [id]/
│       └── route.ts          # GET, PUT, DELETE - Command details
├── mcp-servers/
│   ├── route.ts              # GET, POST - List and configure servers
│   ├── connect/
│   │   └── route.ts          # POST - Connect to server
│   └── [name]/
│       ├── route.ts          # GET, PATCH, DELETE - Server details
│       ├── tools/
│       │   └── route.ts      # GET - List server tools
│       └── resources/
│           └── route.ts      # GET - List server resources
├── tool-presets/
│   ├── route.ts              # GET, POST - List and create presets
│   └── [id]/
│       └── route.ts          # GET, PUT, DELETE - Preset details
├── autocomplete/
│   └── route.ts              # GET - Autocomplete suggestions
├── search/
│   └── route.ts              # GET - Global search
└── health/
    └── route.ts              # GET - Health check (proxies to backend)
```

---

## Core Routes

### Streaming Query

**`POST /api/streaming`**

Proxies SSE streaming requests to Claude Agent API backend.

**Request Body:**
```typescript
{
  prompt: string;
  images?: Array<{
    type: 'base64' | 'url';
    media_type: 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp';
    data: string;
  }>;
  session_id?: string;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  permission_mode?: 'default' | 'acceptEdits' | 'dontAsk' | 'bypassPermissions';
  model?: string;
  max_turns?: number;
  agents?: Record<string, AgentConfig>;
  mcp_servers?: Record<string, McpServerConfig>;
  enable_file_checkpointing?: boolean;
}
```

**Response:**
Server-Sent Events stream (proxied from backend)

**Implementation Notes:**
- Validate API key from request headers or cookies
- Add correlation ID for tracing
- Forward all SSE events from backend to client
- Handle disconnections gracefully
- Log streaming errors

---

## Session Management

### List Sessions

**`GET /api/sessions`**

Get paginated list of sessions with filtering.

**Query Parameters:**
- `mode?: 'brainstorm' | 'code'` - Filter by session mode
- `project_id?: string` - Filter by project (Code mode only)
- `tags?: string[]` - Filter by tags
- `search?: string` - Search in titles and messages
- `page?: number` - Page number (default: 1)
- `page_size?: number` - Items per page (default: 50, max: 100)
- `sort?: 'created_at' | 'updated_at' | 'last_message_at'` - Sort field
- `order?: 'asc' | 'desc'` - Sort order

**Response:**
```typescript
{
  sessions: Array<{
    id: string;
    mode: 'brainstorm' | 'code';
    status: 'active' | 'completed' | 'error';
    project_id?: string;
    title?: string;
    created_at: string;
    updated_at: string;
    last_message_at?: string;
    total_turns: number;
    total_cost_usd?: number;
    parent_session_id?: string;
    tags: string[];
    duration_ms?: number; // Query execution time
    usage?: TokenUsage; // Aggregate token usage
    model_usage?: Record<string, TokenUsage>; // Per-model breakdown
    metadata?: object;
  }>;
  total: number;
  page: number;
  page_size: number;
}

interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}
```

### Create Session

**`POST /api/sessions`**

Create a new session.

**Request Body:**
```typescript
{
  mode: 'brainstorm' | 'code';
  project_id?: string; // Required if mode is 'code'
  title?: string;
  tags?: string[];
}
```

**Response:**
```typescript
{
  session: {
    id: string;
    mode: 'brainstorm' | 'code';
    status: 'active';
    project_id?: string;
    title?: string;
    created_at: string;
    tags: string[];
  }
}
```

### Get Session Details

**`GET /api/sessions/[id]`**

Get detailed information about a specific session.

**Response:**
```typescript
{
  session: {
    id: string;
    mode: 'brainstorm' | 'code';
    status: 'active' | 'completed' | 'error';
    project_id?: string;
    title?: string;
    created_at: string;
    updated_at: string;
    total_turns: number;
    total_cost_usd?: number;
    tags: string[];
  };
  messages: Array<Message>;
  checkpoints: Array<Checkpoint>;
}
```

### Update Session Tags

**`PATCH /api/sessions/[id]/tags`**

Update session tags.

**Request Body:**
```typescript
{
  tags: string[];
}
```

**Response:**
```typescript
{
  session: {
    id: string;
    tags: string[];
    updated_at: string;
  }
}
```

### Promote Session to Code Mode

**`POST /api/sessions/[id]/promote`**

Promote a Brainstorm session to Code mode.

**Request Body:**
```typescript
{
  project_id: string; // Existing project or create new
}
```

**Response:**
```typescript
{
  session: {
    id: string;
    mode: 'code';
    project_id: string;
    updated_at: string;
  }
}
```

### Resume Session

**`POST /api/sessions/[id]/resume`**

Resume an existing session with a new message (proxies to backend).

**Request Body:**
```typescript
{
  prompt: string;
  images?: Array<ImageContent>;
  allowed_tools?: string[];
  permission_mode?: PermissionMode;
}
```

**Response:**
SSE stream (same as `/api/streaming`)

### Fork Session

**`POST /api/sessions/[id]/fork`**

Fork a session from a checkpoint (proxies to backend).

**Request Body:**
```typescript
{
  checkpoint_id?: string; // If not provided, forks from latest
  prompt: string;
  images?: Array<ImageContent>;
}
```

**Response:**
SSE stream with new session ID

---

## Project Management

### List Projects

**`GET /api/projects`**

Get list of all projects for Code mode.

**Query Parameters:**
- `sort?: 'name' | 'created_at' | 'last_accessed_at'`
- `order?: 'asc' | 'desc'`

**Response:**
```typescript
{
  projects: Array<{
    id: string;
    name: string;
    path: string;
    created_at: string;
    last_accessed_at?: string;
    session_count: number;
  }>;
  total: number;
}
```

### Create Project

**`POST /api/projects`**

Create a new project directory.

**Request Body:**
```typescript
{
  name: string;
  path?: string; // Optional custom path, defaults to name
}
```

**Response:**
```typescript
{
  project: {
    id: string;
    name: string;
    path: string;
    created_at: string;
  }
}
```

### Get Project Details

**`GET /api/projects/[id]`**

Get project details including associated sessions.

**Response:**
```typescript
{
  project: {
    id: string;
    name: string;
    path: string;
    created_at: string;
    last_accessed_at?: string;
    session_count: number;
  };
  recent_sessions: Array<Session>; // Last 10 sessions
}
```

---

## Agent Management

### List Agents

**`GET /api/agents`**

Get list of all agent definitions.

**Response:**
```typescript
{
  agents: Array<{
    id: string;
    name: string;
    description: string;
    prompt: string;
    tools?: string[];
    model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
    created_at: string;
    updated_at: string;
    is_shared?: boolean;
    share_url?: string;
  }>;
}
```

### Create Agent

**`POST /api/agents`**

Create a new agent definition.

**Request Body:**
```typescript
{
  name: string;
  description: string;
  prompt: string;
  tools?: string[];
  model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
}
```

**Response:**
```typescript
{
  agent: AgentDefinition;
}
```

### Update Agent

**`PUT /api/agents/[id]`**

Update an existing agent.

**Request Body:** Full agent definition
**Response:** Updated agent

### Delete Agent

**`DELETE /api/agents/[id]`**

Delete an agent.

**Response:** `204 No Content`

### Share Agent

**`POST /api/agents/[id]/share`**

Generate a shareable view-only link for an agent.

**Response:**
```typescript
{
  share_url: string;
  share_token: string;
}
```

---

## Skill Management

Same CRUD structure as agents:
- `GET /api/skills` - List skills
- `POST /api/skills` - Create skill
- `GET /api/skills/[id]` - Get skill
- `PUT /api/skills/[id]` - Update skill
- `DELETE /api/skills/[id]` - Delete skill
- `POST /api/skills/[id]/share` - Share skill

**Skill Schema:**
```typescript
{
  id: string;
  name: string;
  description: string;
  content: string; // Markdown content with YAML frontmatter
  enabled: boolean;
  created_at: string;
  updated_at: string;
  is_shared?: boolean;
  share_url?: string;
}
```

---

## Slash Command Management

Same CRUD structure as skills:
- `GET /api/slash-commands` - List slash commands
- `POST /api/slash-commands` - Create slash command
- `GET /api/slash-commands/[id]` - Get slash command
- `PUT /api/slash-commands/[id]` - Update slash command
- `DELETE /api/slash-commands/[id]` - Delete slash command

**Slash Command Schema:**
```typescript
{
  id: string;
  name: string; // Command name (without slash prefix)
  description: string;
  content: string; // Markdown content with YAML frontmatter
  enabled: boolean;
  created_at: string;
  updated_at: string;
}
```

**Note**: Slash commands use hybrid storage pattern - stored in database for web UI editing, synced to filesystem (`.claude/commands/`) on session start.

---

## MCP Server Management

### List MCP Servers

**`GET /api/mcp-servers`**

Get list of all configured MCP servers with status.

**Response:**
```typescript
{
  servers: Array<{
    name: string;
    type: 'stdio' | 'sse' | 'http';
    status: 'connected' | 'failed' | 'idle' | 'connecting';
    error?: string;
    tools_count?: number;
    resources_count?: number;
    config: McpServerConfig; // Sanitized (credentials removed)
  }>;
}
```

### Configure MCP Server

**`POST /api/mcp-servers`**

Create or update MCP server configuration.

**Request Body:**
```typescript
{
  name: string;
  type: 'stdio' | 'sse' | 'http';
  config: {
    // stdio
    command?: string;
    args?: string[];
    // remote
    url?: string;
    headers?: Record<string, string>;
    // environment
    env?: Record<string, string>;
  };
}
```

**Response:**
```typescript
{
  server: McpServerConfig;
}
```

### Connect to MCP Server

**`POST /api/mcp-servers/connect`**

Initiate connection to an MCP server (for testing).

**Request Body:**
```typescript
{
  name: string; // Existing server name
}
```

**Response:**
```typescript
{
  status: 'connected' | 'failed';
  tools: Array<McpTool>;
  resources: Array<McpResource>;
  error?: string;
}
```

### Get Server Tools

**`GET /api/mcp-servers/[name]/tools`**

Get list of tools provided by a specific MCP server.

**Response:**
```typescript
{
  tools: Array<{
    name: string;
    description: string;
    input_schema: object;
  }>;
}
```

### Get Server Resources

**`GET /api/mcp-servers/[name]/resources`**

Get list of resources provided by a specific MCP server.

**Response:**
```typescript
{
  resources: Array<{
    uri: string;
    name: string;
    description?: string;
    mime_type?: string;
  }>;
}
```

### Read Server Resource

**`GET /api/mcp-servers/[name]/resources/[uri]`**

Read specific resource content from an MCP server.

**Parameters:**
- `name` - Server name identifier
- `uri` - Resource URI (URL encoded)

**Response:**
```typescript
{
  uri: string;
  mimeType?: string;
  text?: string; // Resource content
}
```

---

## Tool Preset Management

### List Tool Presets

**`GET /api/tool-presets`**

Get list of saved tool presets.

**Response:**
```typescript
{
  presets: Array<{
    id: string;
    name: string;
    description?: string;
    tools: string[];
    is_default: boolean;
    created_at: string;
  }>;
}
```

### Create Tool Preset

**`POST /api/tool-presets`**

Save a new tool preset.

**Request Body:**
```typescript
{
  name: string;
  description?: string;
  tools: string[];
  is_default?: boolean;
}
```

**Response:**
```typescript
{
  preset: ToolPreset;
}
```

### Update Tool Preset

**`PUT /api/tool-presets/[id]`**

Update an existing preset.

**Request Body:** Full preset definition
**Response:** Updated preset

### Delete Tool Preset

**`DELETE /api/tool-presets/[id]`**

Delete a preset.

**Response:** `204 No Content`

---

## Autocomplete & Search

### Autocomplete Suggestions

**`GET /api/autocomplete`**

Get autocomplete suggestions for @ and / triggers.

**Query Parameters:**
- `query: string` - Search query
- `type?: 'agent' | 'mcp_server' | 'mcp_tool' | 'mcp_resource' | 'file' | 'skill' | 'slash_command' | 'preset'` - Filter by type

**Response:**
```typescript
{
  suggestions: Array<{
    type: 'agent' | 'mcp_server' | 'mcp_tool' | 'mcp_resource' | 'file' | 'skill' | 'slash_command' | 'preset';
    id: string;
    label: string;
    description?: string;
    icon?: string;
    category?: string;
    recently_used?: boolean;
    insert_text: string;
  }>;
}
```

### Global Search

**`GET /api/search`**

Global search across all entities.

**Query Parameters:**
- `q: string` - Search query
- `categories?: string[]` - Filter by category (sessions, agents, skills, etc.)
- `limit?: number` - Max results (default: 50)

**Response:**
```typescript
{
  results: Array<{
    type: 'session' | 'agent' | 'skill' | 'mcp_server' | 'file';
    id: string;
    title: string;
    description?: string;
    url: string; // Frontend route
    highlights?: string[]; // Matched text snippets
  }>;
  total: number;
}
```

---

## Health Check

### Health Check

**`GET /api/health`**

Health check endpoint (proxies to backend API).

**Response:**
```typescript
{
  status: 'ok' | 'degraded' | 'unhealthy';
  backend: {
    status: 'ok' | 'error';
    latency_ms?: number;
  };
  database: {
    status: 'ok' | 'error';
  };
  redis: {
    status: 'ok' | 'error';
  };
}
```

---

## Error Handling

All BFF routes follow consistent error response format:

```typescript
{
  error: {
    code: string; // ERROR_CODE
    message: string; // User-friendly message
    details?: object; // Optional additional context
  }
}
```

**Common Error Codes:**
- `INVALID_API_KEY` - API key missing or invalid
- `SESSION_NOT_FOUND` - Session ID does not exist
- `PROJECT_NOT_FOUND` - Project ID does not exist
- `VALIDATION_ERROR` - Request body validation failed
- `BACKEND_ERROR` - Error from Claude Agent API backend
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Unexpected server error

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (for deletes)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid API key)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error
- `502` - Bad Gateway (backend unavailable)
- `504` - Gateway Timeout (backend timeout)

---

## Authentication Flow

1. **Client stores API key** in localStorage
2. **Client sends API key** in header with each request:
   ```
   X-API-Key: <api-key>
   ```
3. **BFF validates API key** by calling backend health check or caching validity
4. **BFF forwards API key** to backend in subsequent requests
5. **BFF returns 401** if API key is missing or invalid

**Optional Enhancement:** Use HTTP-only cookies for API key storage (more secure than localStorage).

---

## Rate Limiting

BFF routes implement rate limiting to protect backend:

- **Per-route limits:**
  - `/api/streaming`: 20 requests/minute
  - `/api/sessions`: 100 requests/minute
  - `/api/autocomplete`: 60 requests/minute
  - All others: 50 requests/minute

- **Headers returned:**
  ```
  X-RateLimit-Limit: 20
  X-RateLimit-Remaining: 15
  X-RateLimit-Reset: 1641024000
  ```

---

## Caching Strategy

**Redis caching for:**
- Session metadata (1 hour TTL)
- Agent/skill/preset lists (5 minute TTL)
- MCP server status (30 second TTL)
- Autocomplete results (1 minute TTL)

**Cache invalidation:**
- On create/update/delete operations
- On backend errors (clear affected cache keys)
- Manual invalidation via internal endpoint

---

## Implementation Notes

1. **Use Next.js Edge Runtime** for lightweight routes (health check, autocomplete)
2. **Use Node.js Runtime** for routes requiring streaming or complex logic
3. **Implement request logging** with correlation IDs for tracing
4. **Add OpenTelemetry** for distributed tracing
5. **Use Zod** for request/response validation
6. **Implement circuit breakers** for backend calls
7. **Add request/response transformers** as middleware
8. **Use connection pooling** for database queries

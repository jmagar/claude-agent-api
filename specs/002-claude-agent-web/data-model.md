# Data Model: Claude Agent Web Interface

**Feature Branch**: `002-claude-agent-web`
**Date**: 2026-01-10

## Overview

This document defines the data model for the Claude Agent Web Interface, including TypeScript types, Zod schemas, database entities (managed by backend API), component props, and state management structures.

---

## Frontend Type Definitions (TypeScript)

### Core Message Types

```typescript
type MessageRole = 'user' | 'assistant' | 'system';

type ContentBlockType = 'text' | 'thinking' | 'tool_use' | 'tool_result';

interface BaseContentBlock {
  type: ContentBlockType;
}

interface TextBlock extends BaseContentBlock {
  type: 'text';
  text: string;
}

interface ThinkingBlock extends BaseContentBlock {
  type: 'thinking';
  thinking: string;
}

interface ToolUseBlock extends BaseContentBlock {
  type: 'tool_use';
  id: string;
  name: string;
  input: Record<string, unknown>;
}

interface ToolResultBlock extends BaseContentBlock {
  type: 'tool_result';
  tool_use_id: string;
  content: string | Record<string, unknown>;
  is_error?: boolean;
}

type ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock;

interface Message {
  id: string;
  role: MessageRole;
  content: ContentBlock[];
  uuid?: string; // For checkpoints
  parent_tool_use_id?: string; // For subagent messages
  model?: string;
  usage?: UsageMetrics;
  created_at: Date;
}

interface UsageMetrics {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens?: number;
  cache_creation_input_tokens?: number;
}
```

### Session Types

```typescript
type SessionMode = 'brainstorm' | 'code';
type SessionStatus = 'active' | 'completed' | 'error';

interface Session {
  id: string;
  mode: SessionMode;
  status: SessionStatus;
  project_id?: string; // Only for code mode
  title?: string; // Auto-generated or user-provided
  created_at: Date;
  updated_at: Date;
  last_message_at?: Date;
  total_turns: number;
  total_cost_usd?: number;
  parent_session_id?: string; // For forked sessions
  tags: string[];
  duration_ms?: number; // Query execution time
  usage?: TokenUsage; // Aggregate token usage
  model_usage?: Record<string, TokenUsage>; // Per-model breakdown
  metadata?: Record<string, unknown>;
}

interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}

interface Project {
  id: string;
  name: string;
  path: string; // Relative to WORKSPACE_BASE_DIR
  created_at: Date;
  session_count: number;
  last_accessed_at?: Date;
}
```

### Tool & Permission Types

```typescript
type PermissionMode = 'default' | 'acceptEdits' | 'dontAsk' | 'bypassPermissions';

type ToolStatus = 'idle' | 'running' | 'success' | 'error';

interface ToolCall {
  id: string;
  name: string;
  status: ToolStatus;
  input: Record<string, unknown>;
  output?: string | Record<string, unknown>;
  error?: string;
  started_at?: Date;
  duration_ms?: number;
  parent_tool_use_id?: string; // For threading visualization
}

interface ToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  server?: string; // MCP server name (undefined for built-in tools)
  enabled: boolean;
}

interface ToolPreset {
  id: string;
  name: string;
  description?: string;
  tools: string[]; // Tool names
  created_at: Date;
  is_default?: boolean;
}
```

### MCP Server Types

```typescript
type McpTransportType = 'stdio' | 'sse' | 'http';
type McpServerStatus = 'active' | 'failed' | 'disabled';

interface McpServerConfig {
  id: string;
  name: string;
  type: McpTransportType;

  // Stdio transport
  command?: string;
  args?: string[];

  // Remote transports
  url?: string;
  headers?: Record<string, string>;

  // Environment
  env?: Record<string, string>;

  // Status tracking
  enabled: boolean;
  status: McpServerStatus;
  error?: string; // Error message if status is 'failed'

  // Metadata
  created_at: Date;
  updated_at: Date;

  // UI state (runtime)
  tools_count?: number;
  resources_count?: number;
}

interface McpTool {
  name: string;
  description: string;
  server: string;
  input_schema: Record<string, unknown>;
}

interface McpResource {
  uri: string;
  name: string;
  description?: string;
  mime_type?: string;
  server: string;
}
```

### Agent & Skill Types

```typescript
interface AgentDefinition {
  id: string;
  name: string;
  description: string; // When to use this agent
  prompt: string; // System prompt
  tools?: string[]; // Allowed tools (inherits if undefined)
  model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
  created_at: Date;
  updated_at: Date;
  is_shared?: boolean;
  share_url?: string;
}

interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  content: string; // Markdown content
  created_at: Date;
  updated_at: Date;
  is_shared?: boolean;
  share_url?: string;
}

interface SlashCommand {
  id: string;
  name: string; // Command name (e.g., "compact")
  description: string;
  content: string; // Full markdown content with YAML frontmatter
  enabled: boolean;
  created_at: Date;
  updated_at: Date;
}

// NOTE: Slash commands use hybrid storage pattern:
// - Stored in PostgreSQL for web UI editing
// - Synchronized to filesystem (.claude/commands/) on session start
// - SDK loads from filesystem as required
```

### Checkpoint Types

```typescript
interface Checkpoint {
  id: string; // UUID
  session_id: string;
  user_message_uuid: string;
  created_at: Date;
  files_modified: string[];
  label?: string; // User-provided label
}
```

### Artifact Types

```typescript
type ArtifactType = 'code' | 'markdown' | 'diagram' | 'json' | 'other';

interface Artifact {
  id: string;
  type: ArtifactType;
  language?: string; // For code artifacts (typescript, python, etc.)
  content: string;
  title?: string;
  created_at: Date;
  message_id: string; // Associated message
}
```

### Autocomplete Types

```typescript
type AutocompleteEntityType =
  | 'agent'
  | 'mcp_server'
  | 'mcp_tool'
  | 'mcp_resource'
  | 'file'
  | 'skill'
  | 'slash_command'
  | 'preset';

interface AutocompleteItem {
  type: AutocompleteEntityType;
  id: string;
  label: string;
  description?: string;
  icon?: string;
  category?: string;
  recently_used?: boolean;
  insert_text: string; // Text to insert when selected
}
```

---

## Zod Validation Schemas

### API Request Schemas

```typescript
import { z } from 'zod';

// Query request to Claude Agent API
export const QueryRequestSchema = z.object({
  prompt: z.string().min(1).max(100000),
  images: z.array(z.object({
    type: z.enum(['base64', 'url']),
    media_type: z.enum(['image/jpeg', 'image/png', 'image/gif', 'image/webp']),
    data: z.string(),
  })).optional(),
  session_id: z.string().uuid().optional(),

  // Tool configuration
  allowed_tools: z.array(z.string()).default([]),
  disallowed_tools: z.array(z.string()).default([]),

  // Permissions
  permission_mode: z.enum(['default', 'acceptEdits', 'dontAsk', 'bypassPermissions']).default('default'),

  // Model selection
  model: z.string().optional(),

  // Execution limits
  max_turns: z.number().int().min(1).max(1000).optional(),
  cwd: z.string().optional(),

  // Subagents
  agents: z.record(z.object({
    description: z.string(),
    prompt: z.string(),
    tools: z.array(z.string()).optional(),
    model: z.enum(['sonnet', 'opus', 'haiku', 'inherit']).optional(),
  })).optional(),

  // MCP servers
  mcp_servers: z.record(z.object({
    type: z.enum(['stdio', 'sse', 'http']).default('stdio'),
    command: z.string().optional(),
    args: z.array(z.string()).optional(),
    url: z.string().url().optional(),
    headers: z.record(z.string()).optional(),
    env: z.record(z.string()).optional(),
  })).optional(),

  // File checkpointing
  enable_file_checkpointing: z.boolean().default(false),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;

// Session creation request (BFF)
export const CreateSessionRequestSchema = z.object({
  mode: z.enum(['brainstorm', 'code']).default('brainstorm'),
  project_id: z.string().uuid().optional(),
  title: z.string().max(200).optional(),
  tags: z.array(z.string()).default([]),
});

export type CreateSessionRequest = z.infer<typeof CreateSessionRequestSchema>;

// Project creation request (BFF)
export const CreateProjectRequestSchema = z.object({
  name: z.string().min(1).max(100),
  path: z.string().optional(), // Defaults to name if not provided
});

export type CreateProjectRequest = z.infer<typeof CreateProjectRequestSchema>;
```

### Component Props Schemas

```typescript
// Message component props
export const MessagePropsSchema = z.object({
  message: z.custom<Message>(),
  showThreading: z.boolean().default(true),
  onRetryTool: z.function().args(z.string()).returns(z.void()).optional(),
  onFork: z.function().args(z.string()).returns(z.void()).optional(),
});

export type MessageProps = z.infer<typeof MessagePropsSchema>;

// Tool call card props
export const ToolCallCardPropsSchema = z.object({
  toolCall: z.custom<ToolCall>(),
  collapsed: z.boolean().default(false),
  onToggle: z.function().args().returns(z.void()).optional(),
  onRetry: z.function().args().returns(z.void()).optional(),
  onApprove: z.function().args().returns(z.void()).optional(),
  onDeny: z.function().args().returns(z.void()).optional(),
  needsApproval: z.boolean().default(false),
});

export type ToolCallCardProps = z.infer<typeof ToolCallCardPropsSchema>;
```

---

## State Management Types

### React Context Types

```typescript
// Auth context
interface AuthContextType {
  apiKey: string | null;
  setApiKey: (key: string) => void;
  clearApiKey: () => void;
  isAuthenticated: boolean;
}

// Settings context
interface SettingsContextType {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;

  threadingMode: 'always' | 'hover' | 'adaptive' | 'toggle';
  setThreadingMode: (mode: 'always' | 'hover' | 'adaptive' | 'toggle') => void;

  defaultPermissionMode: PermissionMode;
  setDefaultPermissionMode: (mode: PermissionMode) => void;

  workspaceBaseDir: string;
  setWorkspaceBaseDir: (dir: string) => void;

  messageDensity: 'compact' | 'comfortable' | 'spacious';
  setMessageDensity: (density: 'compact' | 'comfortable' | 'spacious') => void;
}

// Active session context
interface ActiveSessionContextType {
  session: Session | null;
  messages: Message[];
  isStreaming: boolean;
  sendMessage: (prompt: string, images?: File[]) => Promise<void>;
  interruptSession: () => Promise<void>;
  forkSession: (checkpointId: string) => Promise<Session>;

  // Tool state
  activeTools: Set<string>;
  permissionMode: PermissionMode;
  setPermissionMode: (mode: PermissionMode) => void;

  // MCP state
  connectedServers: McpServerConfig[];
}
```

### TanStack Query Keys

```typescript
// Query key factories for React Query
export const queryKeys = {
  sessions: {
    all: ['sessions'] as const,
    lists: () => [...queryKeys.sessions.all, 'list'] as const,
    list: (mode: SessionMode) => [...queryKeys.sessions.lists(), mode] as const,
    details: () => [...queryKeys.sessions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.sessions.details(), id] as const,
  },

  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.projects.all, id] as const,
  },

  agents: {
    all: ['agents'] as const,
    lists: () => [...queryKeys.agents.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.agents.all, id] as const,
  },

  mcpServers: {
    all: ['mcp-servers'] as const,
    lists: () => [...queryKeys.mcpServers.all, 'list'] as const,
    detail: (name: string) => [...queryKeys.mcpServers.all, name] as const,
    tools: (name: string) => [...queryKeys.mcpServers.detail(name), 'tools'] as const,
  },

  toolPresets: {
    all: ['tool-presets'] as const,
    lists: () => [...queryKeys.toolPresets.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.toolPresets.all, id] as const,
  },
} as const;
```

---

## Backend Data Structures (PostgreSQL)

These entities are managed by the Claude Agent API backend but relevant to frontend queries:

### Session Table

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    mode VARCHAR(20) NOT NULL DEFAULT 'brainstorm', -- 'brainstorm' or 'code'
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    project_id UUID REFERENCES projects(id),
    title VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    total_turns INT NOT NULL DEFAULT 0,
    total_cost_usd DECIMAL(10, 6),
    parent_session_id UUID REFERENCES sessions(id),
    tags TEXT[] DEFAULT '{}',
    duration_ms INT, -- Query execution time in milliseconds
    usage JSONB, -- Aggregate token usage
    model_usage JSONB, -- Per-model token breakdown
    metadata JSONB,
    owner_api_key VARCHAR(255) NOT NULL -- API key ownership
);

CREATE INDEX idx_sessions_mode ON sessions(mode);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_project_id ON sessions(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_sessions_tags ON sessions USING GIN(tags);
CREATE INDEX idx_sessions_last_message_at ON sessions(last_message_at);
CREATE INDEX idx_sessions_owner_api_key ON sessions(owner_api_key);
```

### Project Table

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    path VARCHAR(500) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ,
    metadata JSONB
);
```

### Agent Configuration Table

```sql
CREATE TABLE agent_definitions (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    prompt TEXT NOT NULL,
    tools TEXT[], -- Array of tool names
    model VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_shared BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(64) UNIQUE
);
```

### Skill Definition Table

```sql
CREATE TABLE skill_definitions (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    content TEXT NOT NULL, -- Markdown content with YAML frontmatter
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_shared BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(64) UNIQUE,
    metadata JSONB
);

-- NOTE: Skills use hybrid storage pattern:
-- Database stores content for web UI editing
-- Backend syncs to filesystem (.claude/skills/) on session start
```

### Tool Preset Table

```sql
CREATE TABLE tool_presets (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    allowed_tools TEXT[] NOT NULL, -- Array of tool names
    disallowed_tools TEXT[] NOT NULL DEFAULT '{}',
    is_system BOOLEAN NOT NULL DEFAULT FALSE, -- Built-in preset
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);
```

### Slash Command Table

```sql
CREATE TABLE slash_commands (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    content TEXT NOT NULL, -- Markdown content with YAML frontmatter
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- NOTE: Slash commands use hybrid storage pattern:
-- Database stores content for web UI editing
-- Backend syncs to filesystem (.claude/commands/) on session start
```

### MCP Server Configuration Table

```sql
CREATE TABLE mcp_server_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    transport_type VARCHAR(20) NOT NULL, -- 'stdio', 'sse', 'http'

    -- Stdio fields
    command VARCHAR(500),
    args TEXT[],

    -- SSE/HTTP fields
    url VARCHAR(1000),
    headers JSONB,

    -- Common fields
    env JSONB, -- Environment variables with ${VAR:-default} support
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'failed', 'disabled'
    error TEXT, -- Error message if status='failed'

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_mcp_servers_status ON mcp_server_configs(status);
CREATE INDEX idx_mcp_servers_enabled ON mcp_server_configs(enabled) WHERE enabled = TRUE;
```

---

## Redis Cache Structures

### Active Session Metadata

```
Key: session_meta:{session_id}
TTL: 3600 seconds (1 hour)
Value: JSON
{
  "mode": "code",
  "project_id": "uuid",
  "title": "Building API endpoints",
  "last_activity": "2026-01-10T12:00:00Z",
  "connected_mcp_servers": ["postgres", "browser"]
}
```

### User Preferences Cache

```
Key: user_prefs:{user_id}
TTL: 86400 seconds (24 hours)
Value: JSON
{
  "theme": "dark",
  "threading_mode": "always",
  "default_permission_mode": "ask_before_edits",
  "workspace_base_dir": "/workspaces"
}
```

### Autocomplete Recently Used

```
Key: autocomplete_recent:{user_id}
Type: ZSET (sorted set)
Score: timestamp
Members: entity_type:entity_id pairs
```

---

## Next.js BFF API Routes

### Route Type Definitions

```typescript
// GET /api/sessions
interface GetSessionsResponse {
  sessions: Session[];
  total: number;
  page: number;
  page_size: number;
}

// GET /api/sessions/[id]
interface GetSessionResponse {
  session: Session;
  messages: Message[];
  checkpoints: Checkpoint[];
}

// POST /api/sessions
interface CreateSessionResponse {
  session: Session;
}

// GET /api/projects
interface GetProjectsResponse {
  projects: Project[];
}

// POST /api/projects
interface CreateProjectResponse {
  project: Project;
}

// GET /api/agents
interface GetAgentsResponse {
  agents: AgentDefinition[];
}

// POST /api/agents
interface CreateAgentResponse {
  agent: AgentDefinition;
  share_url?: string;
}

// GET /api/mcp-servers
interface GetMcpServersResponse {
  servers: McpServerConfig[];
}

// POST /api/mcp-servers/connect
interface ConnectMcpServerRequest {
  config: Omit<McpServerConfig, 'status' | 'error'>;
}

interface ConnectMcpServerResponse {
  server: McpServerConfig;
  tools: McpTool[];
  resources: McpResource[];
}

// GET /api/tool-presets
interface GetToolPresetsResponse {
  presets: ToolPreset[];
}

// POST /api/tool-presets
interface CreateToolPresetResponse {
  preset: ToolPreset;
}
```

---

## Entity Relationships

```
Session (1) ──────< (N) Message
    │
    └──< (N) Checkpoint
    │
    └──< (0..1) Session (parent_session_id for forks)
    │
    └──> (0..1) Project (for Code mode sessions)

Project (1) ──────< (N) Session

AgentDefinition (N) ──────< (N) Session (via session metadata)

McpServerConfig (N) ──────< (N) Session (via active connections)

ToolPreset (1) ──────< (N) Session (via session metadata)
```

---

## Architecture Patterns

### Hybrid Storage for SDK-Required Filesystem Features

**Challenge**: Claude Agent SDK requires certain features to be filesystem-based (skills in `.claude/skills/`, slash commands in `.claude/commands/`), but web UI users need database-backed CRUD operations for easy management.

**Solution**: Hybrid Storage Pattern

#### Skills Architecture

1. **Database Storage**: Skills stored in `skill_definitions` table for web UI editing
2. **Session Initialization**: On session start, backend reads enabled skills from database
3. **Filesystem Sync**: Backend writes skills to session-scoped `.claude/skills/` directory
4. **SDK Loading**: Claude Agent SDK loads skills from filesystem as normal
5. **Isolation**: Each session gets its own skills directory (e.g., `/tmp/claude-sessions/{session_id}/.claude/skills/`)
6. **Cleanup**: Skills directory deleted on session end

**Benefits**:
- Web UI users can create/edit/delete skills via UI
- Multi-tenancy supported (each user has own skills)
- Backup/restore easy (skills in database)
- SDK requirements satisfied (filesystem-based loading)

#### Slash Commands Architecture

Same hybrid pattern as skills:
1. Database: `slash_commands` table
2. Sync: DB → `.claude/commands/` on session start
3. SDK loads from filesystem

#### Service Implementation

**`apps/api/services/skills_sync.py`**:
```python
async def sync_skills_to_filesystem(session_id: UUID, user_id: str) -> Path:
    """Sync enabled skills from database to session filesystem."""
    skills_dir = Path(f"/tmp/claude-sessions/{session_id}/.claude/skills")
    skills_dir.mkdir(parents=True, exist_ok=True)

    skills = await get_enabled_skills(user_id)
    for skill in skills:
        skill_file = skills_dir / f"{skill.name}.md"
        skill_file.write_text(skill.content)

    return skills_dir
```

**`apps/api/services/commands_sync.py`**:
```python
async def sync_commands_to_filesystem(session_id: UUID, user_id: str) -> Path:
    """Sync enabled slash commands from database to session filesystem."""
    commands_dir = Path(f"/tmp/claude-sessions/{session_id}/.claude/commands")
    commands_dir.mkdir(parents=True, exist_ok=True)

    commands = await get_enabled_commands(user_id)
    for command in commands:
        command_file = commands_dir / f"{command.name}.md"
        command_file.write_text(command.content)

    return commands_dir
```

---

## Frontend localStorage Schema

```typescript
// Keys stored in localStorage
interface LocalStorageSchema {
  'auth.apiKey': string; // Claude Agent API key
  'settings.theme': 'light' | 'dark';
  'settings.threadingMode': 'always' | 'hover' | 'adaptive' | 'toggle';
  'settings.permissionMode': PermissionMode;
  'settings.workspaceBaseDir': string;
  'settings.messageDensity': 'compact' | 'comfortable' | 'spacious';
  'drafts.{sessionId}': string; // Draft message content
  'recentSessions': string[]; // Array of session IDs
  'commandPalette.recentCommands': string[]; // Recent command IDs
}
```

---

## Type Guards & Utilities

```typescript
// Type guard for content blocks
export function isToolUseBlock(block: ContentBlock): block is ToolUseBlock {
  return block.type === 'tool_use';
}

export function isToolResultBlock(block: ContentBlock): block is ToolResultBlock {
  return block.type === 'tool_result';
}

export function isTextBlock(block: ContentBlock): block is TextBlock {
  return block.type === 'text';
}

export function isThinkingBlock(block: ContentBlock): block is ThinkingBlock {
  return block.type === 'thinking';
}

// Session mode helpers
export function isCodeMode(session: Session): boolean {
  return session.mode === 'code';
}

export function isBrainstormMode(session: Session): boolean {
  return session.mode === 'brainstorm';
}
```

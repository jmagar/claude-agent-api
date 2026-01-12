// Agent types
export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  prompt: string;
  tools?: string[];
  model?: 'sonnet' | 'opus' | 'haiku' | 'inherit';
  created_at: Date | string;
  updated_at: Date | string;
  is_shared?: boolean;
  share_url?: string;
}

// Skill types
export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  content: string;
  enabled: boolean;
  created_at: Date | string;
  updated_at: Date | string;
  is_shared?: boolean;
  share_url?: string;
}

// Slash command types
export interface SlashCommandDefinition {
  id: string;
  name: string;
  description: string;
  content: string;
  enabled: boolean;
  created_at: Date | string;
  updated_at: Date | string;
}

// Project types
export interface Project {
  id: string;
  name: string;
  path: string;
  created_at: Date | string;
  last_accessed_at?: Date | string;
  session_count?: number;
  metadata?: Record<string, unknown>;
}

// Session types
export interface Session {
  id: string;
  mode: 'brainstorm' | 'code';
  status: 'active' | 'completed' | 'error';
  project_id?: string;
  title?: string;
  created_at: Date | string;
  updated_at: Date | string;
  last_message_at?: Date | string;
  total_turns: number;
  total_cost_usd?: number;
  parent_session_id?: string;
  tags: string[];
  duration_ms?: number;
  usage?: TokenUsage;
  model_usage?: Record<string, TokenUsage>;
  metadata?: Record<string, unknown>;
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}

// Message types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: MessageContent[];
  created_at: Date | string;
  metadata?: Record<string, unknown>;
}

export interface MessageContent {
  type: 'text' | 'thinking' | 'tool_use' | 'tool_result';
  text?: string;
  tool_use_id?: string;
  name?: string;
  input?: Record<string, unknown>;
  content?: unknown;
  is_error?: boolean;
}

// MCP types
export interface McpServerConfig {
  id: string;
  name: string;
  transport_type: 'stdio' | 'sse' | 'http';
  command?: string;
  args?: string[];
  url?: string;
  headers?: Record<string, string>;
  env?: Record<string, string>;
  enabled: boolean;
  status?: 'active' | 'failed' | 'disabled';
  error?: string;
  created_at: Date | string;
  updated_at: Date | string;
  metadata?: Record<string, unknown>;
}

export interface McpTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
}

export interface McpResource {
  uri: string;
  name: string;
  description?: string;
  mime_type?: string;
}

// Tool preset types
export interface ToolPreset {
  id: string;
  name: string;
  description?: string;
  allowed_tools: string[];
  disallowed_tools?: string[];
  is_system?: boolean;
  created_at: Date | string;
}

// API types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// Permission modes
export type PermissionMode = 'default' | 'acceptEdits' | 'dontAsk' | 'bypassPermissions';

// Autocomplete types
export interface AutocompleteSuggestion {
  type:
    | 'agent'
    | 'mcp_server'
    | 'mcp_tool'
    | 'mcp_resource'
    | 'file'
    | 'skill'
    | 'slash_command'
    | 'preset';
  id: string;
  label: string;
  description?: string;
  icon?: string;
  category?: string;
  recently_used?: boolean;
  insert_text: string;
}

// Image types
export interface ImageContent {
  type: 'base64' | 'url';
  media_type: 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp';
  data: string;
}

// Query request
export interface QueryRequest {
  prompt: string;
  images?: ImageContent[];
  session_id?: string;
  allowed_tools?: string[];
  disallowed_tools?: string[];
  permission_mode?: PermissionMode;
  model?: string;
  max_turns?: number;
  agents?: Record<string, unknown>;
  mcp_servers?: Record<string, unknown>;
  enable_file_checkpointing?: boolean;
}

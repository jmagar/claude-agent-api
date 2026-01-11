/**
 * Core TypeScript types for Claude Agent Web Interface
 * Generated from data-model.md
 */

// Message Types
export type MessageRole = "user" | "assistant" | "system";
export type ContentBlockType = "text" | "thinking" | "tool_use" | "tool_result";

export interface BaseContentBlock {
  type: ContentBlockType;
}

export interface TextBlock extends BaseContentBlock {
  type: "text";
  text: string;
}

export interface ThinkingBlock extends BaseContentBlock {
  type: "thinking";
  thinking: string;
}

export interface ToolUseBlock extends BaseContentBlock {
  type: "tool_use";
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface ToolResultBlock extends BaseContentBlock {
  type: "tool_result";
  tool_use_id: string;
  content: string | Record<string, unknown>;
  is_error?: boolean;
}

export type ContentBlock =
  | TextBlock
  | ThinkingBlock
  | ToolUseBlock
  | ToolResultBlock;

// Type Guard Functions

/**
 * Type guard to check if a ContentBlock is a TextBlock.
 * @param block - The content block to check
 * @returns True if the block is a TextBlock
 */
export function isTextBlock(block: ContentBlock): block is TextBlock {
  return block.type === "text";
}

/**
 * Type guard to check if a ContentBlock is a ThinkingBlock.
 * @param block - The content block to check
 * @returns True if the block is a ThinkingBlock
 */
export function isThinkingBlock(block: ContentBlock): block is ThinkingBlock {
  return block.type === "thinking";
}

/**
 * Type guard to check if a ContentBlock is a ToolUseBlock.
 * @param block - The content block to check
 * @returns True if the block is a ToolUseBlock
 */
export function isToolUseBlock(block: ContentBlock): block is ToolUseBlock {
  return block.type === "tool_use";
}

/**
 * Type guard to check if a ContentBlock is a ToolResultBlock.
 * @param block - The content block to check
 * @returns True if the block is a ToolResultBlock
 */
export function isToolResultBlock(
  block: ContentBlock
): block is ToolResultBlock {
  return block.type === "tool_result";
}

export interface UsageMetrics {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens?: number;
  cache_creation_input_tokens?: number;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: ContentBlock[];
  uuid?: string;
  parent_tool_use_id?: string;
  model?: string;
  usage?: UsageMetrics;
  created_at: Date;
}

// Session Types
export type SessionMode = "brainstorm" | "code";
export type SessionStatus = "active" | "completed" | "error";

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}

export interface Session {
  id: string;
  mode: SessionMode;
  status: SessionStatus;
  project_id?: string;
  title?: string;
  created_at: Date;
  updated_at: Date;
  last_message_at?: Date;
  total_turns: number;
  total_cost_usd?: number;
  parent_session_id?: string;
  tags: string[];
  duration_ms?: number;
  usage?: TokenUsage;
  model_usage?: Record<string, TokenUsage>;
  metadata?: Record<string, unknown>;
}

export interface Project {
  id: string;
  name: string;
  path: string;
  created_at: Date;
  session_count: number;
  last_accessed_at?: Date;
}

// Tool & Permission Types
export type PermissionMode =
  | "default"
  | "acceptEdits"
  | "dontAsk"
  | "bypassPermissions";

export type ToolStatus = "idle" | "running" | "success" | "error";

export interface ToolCall {
  id: string;
  name: string;
  status: ToolStatus;
  input: Record<string, unknown>;
  output?: string | Record<string, unknown>;
  error?: string;
  started_at?: Date;
  duration_ms?: number;
  parent_tool_use_id?: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  server?: string;
  enabled: boolean;
}

export interface ToolPreset {
  id: string;
  name: string;
  description?: string;
  tools: string[];
  created_at: Date;
  is_default?: boolean;
}

// MCP Server Types
export type McpTransportType = "stdio" | "sse" | "http";
export type McpServerStatus = "active" | "failed" | "disabled";

export interface McpServerConfig {
  id: string;
  name: string;
  type: McpTransportType;
  command?: string;
  args?: string[];
  url?: string;
  headers?: Record<string, string>;
  env?: Record<string, string>;
  enabled: boolean;
  status: McpServerStatus;
  error?: string;
  created_at: Date;
  updated_at: Date;
  tools_count?: number;
  resources_count?: number;
}

export interface McpTool {
  name: string;
  description: string;
  server: string;
  input_schema: Record<string, unknown>;
}

export interface McpResource {
  uri: string;
  name: string;
  description?: string;
  mime_type?: string;
  server: string;
}

// Agent & Skill Types
export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  prompt: string;
  tools?: string[];
  model?: "sonnet" | "opus" | "haiku" | "inherit";
  created_at: Date;
  updated_at: Date;
  is_shared?: boolean;
  share_url?: string;
}

export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  content: string;
  created_at: Date;
  updated_at: Date;
  is_shared?: boolean;
  share_url?: string;
}

export interface SlashCommand {
  id: string;
  name: string;
  description: string;
  content: string;
  enabled: boolean;
  created_at: Date;
  updated_at: Date;
}

// Checkpoint Types
export interface Checkpoint {
  id: string;
  session_id: string;
  user_message_uuid: string;
  created_at: Date;
  files_modified: string[];
  label?: string;
}

// Artifact Types
export type ArtifactType = "code" | "markdown" | "diagram" | "json" | "other";

export interface Artifact {
  id: string;
  type: ArtifactType;
  language?: string;
  content: string;
  title?: string;
  created_at: Date;
  message_id: string;
}

// Autocomplete Types
export type AutocompleteEntityType =
  | "agent"
  | "mcp_server"
  | "mcp_tool"
  | "mcp_resource"
  | "file"
  | "skill"
  | "slash_command"
  | "preset";

export interface AutocompleteItem {
  type: AutocompleteEntityType;
  id: string;
  label: string;
  description?: string;
  icon?: string;
  category?: string;
  recently_used?: boolean;
  insert_text: string;
}

// Settings Types
export type ThemeMode = "light" | "dark" | "system";
export type ThreadingMode = "always" | "auto" | "never";

export interface UserSettings {
  theme: ThemeMode;
  threading_mode: ThreadingMode;
  workspace_base_dir?: string;
  default_permission_mode: PermissionMode;
  default_model?: string;
  auto_compact_threshold?: number;
}

// Streaming Event Types
export type StreamEventType =
  | "init"
  | "message"
  | "message_delta"
  | "tool_start"
  | "tool_end"
  | "thinking_start"
  | "thinking_delta"
  | "thinking_end"
  | "error"
  | "result";

export interface StreamEvent {
  event: StreamEventType;
  data: unknown;
}

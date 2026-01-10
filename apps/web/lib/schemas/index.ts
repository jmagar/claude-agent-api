/**
 * Zod validation schemas for API requests and responses
 */
import { z } from "zod";

// Query Request Schema
export const QueryRequestSchema = z.object({
  prompt: z.string().min(1).max(100000),
  images: z
    .array(
      z.object({
        type: z.enum(["base64", "url"]),
        media_type: z.enum([
          "image/jpeg",
          "image/png",
          "image/gif",
          "image/webp",
        ]),
        data: z.string(),
      })
    )
    .optional(),
  session_id: z.string().uuid().optional(),
  allowed_tools: z.array(z.string()).default([]),
  disallowed_tools: z.array(z.string()).default([]),
  permission_mode: z
    .enum(["default", "acceptEdits", "dontAsk", "bypassPermissions"])
    .default("default"),
  model: z.string().optional(),
  max_turns: z.number().int().min(1).max(1000).optional(),
  cwd: z.string().optional(),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;

// Session Schemas
export const SessionSchema = z.object({
  id: z.string().uuid(),
  mode: z.enum(["brainstorm", "code"]),
  status: z.enum(["active", "completed", "error"]),
  project_id: z.string().uuid().optional(),
  title: z.string().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  last_message_at: z.string().datetime().optional(),
  total_turns: z.number().int().min(0),
  total_cost_usd: z.number().optional(),
  parent_session_id: z.string().uuid().optional(),
  tags: z.array(z.string()),
  duration_ms: z.number().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type SessionResponse = z.infer<typeof SessionSchema>;

// MCP Server Config Schema
export const McpServerConfigSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  type: z.enum(["stdio", "sse", "http"]).default("stdio"),
  command: z.string().optional(),
  args: z.array(z.string()).optional(),
  url: z.string().url().optional(),
  headers: z.record(z.string()).optional(),
  env: z.record(z.string()).optional(),
  enabled: z.boolean(),
  status: z.enum(["active", "failed", "disabled"]),
  error: z.string().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  tools_count: z.number().int().min(0).optional(),
  resources_count: z.number().int().min(0).optional(),
});

export type McpServerConfigResponse = z.infer<typeof McpServerConfigSchema>;

// Agent Definition Schema
export const AgentDefinitionSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string(),
  prompt: z.string(),
  tools: z.array(z.string()).optional(),
  model: z.enum(["sonnet", "opus", "haiku", "inherit"]).optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  is_shared: z.boolean().optional(),
  share_url: z.string().url().optional(),
});

export type AgentDefinitionResponse = z.infer<typeof AgentDefinitionSchema>;

// Skill Definition Schema
export const SkillDefinitionSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string(),
  content: z.string(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
  is_shared: z.boolean().optional(),
  share_url: z.string().url().optional(),
});

export type SkillDefinitionResponse = z.infer<typeof SkillDefinitionSchema>;

// Project Schema
export const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  path: z.string(),
  created_at: z.string().datetime(),
  session_count: z.number().int().min(0),
  last_accessed_at: z.string().datetime().optional(),
});

export type ProjectResponse = z.infer<typeof ProjectSchema>;

// Error Response Schema
export const ErrorResponseSchema = z.object({
  error: z.string(),
  detail: z.string().optional(),
  correlation_id: z.string().optional(),
});

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

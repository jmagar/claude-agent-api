/**
 * Zod validation schemas for API requests and responses
 */
import { z } from "zod";

const DateTimeSchema = z
  .union([z.string().datetime(), z.date()])
  .transform((value) => (value instanceof Date ? value : new Date(value)));

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
  agents: z
    .record(
      z.object({
        description: z.string(),
        prompt: z.string(),
        tools: z.array(z.string()).optional(),
        model: z.enum(["sonnet", "opus", "haiku", "inherit"]).optional(),
      })
    )
    .optional(),
  mcp_servers: z
    .record(
      z.object({
        type: z.enum(["stdio", "sse", "http"]).default("stdio"),
        command: z.string().optional(),
        args: z.array(z.string()).optional(),
        url: z.string().url().optional(),
        headers: z.record(z.string()).optional(),
        env: z.record(z.string()).optional(),
      })
    )
    .optional(),
  enable_file_checkpointing: z.boolean().default(false),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;

export const CreateSessionRequestSchema = z.object({
  mode: z.enum(["brainstorm", "code"]).default("brainstorm"),
  project_id: z.string().uuid().optional(),
  title: z.string().max(200).optional(),
  tags: z.array(z.string()).default([]),
});

export const UpdateSessionRequestSchema = z
  .object({
    title: z.string().max(200).optional(),
    tags: z.array(z.string()).optional(),
  })
  .refine((data) => data.title || data.tags, {
    message: "At least one field (title or tags) must be provided",
  });

export type CreateSessionRequest = z.infer<typeof CreateSessionRequestSchema>;
export type UpdateSessionRequest = z.infer<typeof UpdateSessionRequestSchema>;

export const CreateProjectRequestSchema = z.object({
  name: z.string().min(1).max(100),
  path: z.string().optional(),
});

export const UpdateProjectRequestSchema = z
  .object({
    name: z.string().min(1).max(100).optional(),
    metadata: z.record(z.unknown()).optional(),
  })
  .refine((data) => data.name || data.metadata, {
    message: "At least one field (name or metadata) must be provided",
  });

export type CreateProjectRequest = z.infer<typeof CreateProjectRequestSchema>;
export type UpdateProjectRequest = z.infer<typeof UpdateProjectRequestSchema>;

// Session Schemas
export const SessionSchema = z.object({
  id: z.string().uuid(),
  mode: z.enum(["brainstorm", "code"]),
  status: z.enum(["active", "completed", "error"]),
  project_id: z.string().uuid().optional(),
  title: z.string().optional(),
  created_at: DateTimeSchema,
  updated_at: DateTimeSchema,
  last_message_at: DateTimeSchema.optional(),
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
  transport_type: z.enum(["stdio", "sse", "http"]).default("stdio"),
  command: z.string().optional(),
  args: z.array(z.string()).optional(),
  url: z.string().url().optional(),
  headers: z.record(z.string()).optional(),
  env: z.record(z.string()).optional(),
  enabled: z.boolean(),
  status: z.enum(["active", "failed", "disabled"]),
  error: z.string().optional(),
  created_at: DateTimeSchema,
  updated_at: DateTimeSchema,
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
  created_at: DateTimeSchema,
  updated_at: DateTimeSchema,
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
  created_at: DateTimeSchema,
  updated_at: DateTimeSchema,
  is_shared: z.boolean().optional(),
  share_url: z.string().url().optional(),
});

export type SkillDefinitionResponse = z.infer<typeof SkillDefinitionSchema>;

// Project Schema
export const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  path: z.string(),
  created_at: DateTimeSchema,
  session_count: z.number().int().min(0),
  last_accessed_at: DateTimeSchema.optional(),
});

export type ProjectResponse = z.infer<typeof ProjectSchema>;

export const SlashCommandDefinitionSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string(),
  content: z.string(),
  enabled: z.boolean(),
  created_at: DateTimeSchema,
  updated_at: DateTimeSchema,
});

export type SlashCommandDefinitionResponse = z.infer<
  typeof SlashCommandDefinitionSchema
>;

export const ToolPresetSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  allowed_tools: z.array(z.string()),
  disallowed_tools: z.array(z.string()).default([]),
  is_system: z.boolean().optional(),
  created_at: DateTimeSchema,
});

export type ToolPresetResponse = z.infer<typeof ToolPresetSchema>;

// Error Response Schema
export const ErrorResponseSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.unknown()).optional(),
});

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

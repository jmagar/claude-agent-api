import type {
  AgentDefinition,
  Checkpoint,
  McpServerConfig,
  McpTransportType,
  Project,
  Session,
  SkillDefinition,
  SlashCommand,
  ToolPreset,
} from "@/types";

type DateLike = string | Date;

function parseDate(value: DateLike): Date {
  return value instanceof Date ? value : new Date(value);
}

function parseOptionalDate(value?: DateLike | null): Date | undefined {
  if (!value) {
    return undefined;
  }
  return parseDate(value);
}

type SessionInput = Omit<Session, "created_at" | "updated_at" | "last_message_at"> & {
  created_at: DateLike;
  updated_at: DateLike;
  last_message_at?: DateLike;
};

type ProjectInput = Omit<Project, "created_at" | "last_accessed_at"> & {
  created_at: DateLike;
  last_accessed_at?: DateLike;
};

type AgentInput = Omit<AgentDefinition, "created_at" | "updated_at"> & {
  created_at: DateLike;
  updated_at: DateLike;
};

type SkillInput = Omit<SkillDefinition, "created_at" | "updated_at"> & {
  created_at: DateLike;
  updated_at: DateLike;
};

type SlashCommandInput = Omit<SlashCommand, "created_at" | "updated_at"> & {
  created_at: DateLike;
  updated_at: DateLike;
};

type ToolPresetInput = Omit<ToolPreset, "allowed_tools" | "created_at" | "is_system"> & {
  allowed_tools?: string[];
  tools?: string[];
  created_at: DateLike;
  disallowed_tools?: string[];
  is_system?: boolean;
  is_default?: boolean;
};

type McpServerConfigInput = Omit<McpServerConfig, "transport_type" | "created_at" | "updated_at"> & {
  transport_type?: McpTransportType;
  type?: McpTransportType;
  created_at: DateLike;
  updated_at: DateLike;
};

type CheckpointInput = Omit<Checkpoint, "created_at"> & {
  created_at: DateLike;
};

export function mapSession(input: SessionInput): Session {
  return {
    ...input,
    created_at: parseDate(input.created_at),
    updated_at: parseDate(input.updated_at),
    last_message_at: parseOptionalDate(input.last_message_at),
  };
}

export function mapProject(input: ProjectInput): Project {
  return {
    ...input,
    created_at: parseDate(input.created_at),
    last_accessed_at: parseOptionalDate(input.last_accessed_at),
  };
}

export function mapAgentDefinition(input: AgentInput): AgentDefinition {
  return {
    ...input,
    created_at: parseDate(input.created_at),
    updated_at: parseDate(input.updated_at),
  };
}

export function mapSkillDefinition(input: SkillInput): SkillDefinition {
  return {
    ...input,
    created_at: parseDate(input.created_at),
    updated_at: parseDate(input.updated_at),
  };
}

export function mapSlashCommand(input: SlashCommandInput): SlashCommand {
  return {
    ...input,
    created_at: parseDate(input.created_at),
    updated_at: parseDate(input.updated_at),
  };
}

export function mapToolPreset(input: ToolPresetInput): ToolPreset {
  const {
    tools,
    allowed_tools: allowedToolsOverride,
    is_system,
    is_default,
    ...rest
  } = input;
  const allowed_tools = allowedToolsOverride ?? tools ?? [];
  return {
    ...rest,
    allowed_tools,
    disallowed_tools: input.disallowed_tools ?? [],
    created_at: parseDate(input.created_at),
    is_system: is_system ?? is_default,
  };
}

export function mapMcpServerConfig(input: McpServerConfigInput): McpServerConfig {
  const { type, transport_type, ...rest } = input;
  return {
    ...rest,
    transport_type: transport_type ?? type ?? "stdio",
    created_at: parseDate(input.created_at),
    updated_at: parseDate(input.updated_at),
  };
}

export function mapCheckpoint(input: CheckpointInput): Checkpoint {
  return {
    ...input,
    created_at: parseDate(input.created_at),
  };
}

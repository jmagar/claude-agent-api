import type { SessionFilters, SessionMode } from "@/types";

export const queryKeys = {
  sessions: {
    all: ["sessions"] as const,
    lists: () => [...queryKeys.sessions.all, "list"] as const,
    list: (filters: SessionMode | SessionFilters) =>
      [...queryKeys.sessions.lists(), filters] as const,
    details: () => [...queryKeys.sessions.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.sessions.details(), id] as const,
    checkpoints: (id: string) =>
      [...queryKeys.sessions.detail(id), "checkpoints"] as const,
  },
  projects: {
    all: ["projects"] as const,
    lists: () => [...queryKeys.projects.all, "list"] as const,
    detail: (id: string) => [...queryKeys.projects.all, id] as const,
  },
  agents: {
    all: ["agents"] as const,
    lists: () => [...queryKeys.agents.all, "list"] as const,
    detail: (id: string) => [...queryKeys.agents.all, id] as const,
  },
  skills: {
    all: ["skills"] as const,
    lists: () => [...queryKeys.skills.all, "list"] as const,
    detail: (id: string) => [...queryKeys.skills.all, id] as const,
  },
  slashCommands: {
    all: ["slash-commands"] as const,
    lists: () => [...queryKeys.slashCommands.all, "list"] as const,
    detail: (id: string) => [...queryKeys.slashCommands.all, id] as const,
  },
  mcpServers: {
    all: ["mcp-servers"] as const,
    lists: () => [...queryKeys.mcpServers.all, "list"] as const,
    detail: (name: string) => [...queryKeys.mcpServers.all, name] as const,
    tools: (name: string) => [...queryKeys.mcpServers.detail(name), "tools"] as const,
  },
  toolPresets: {
    all: ["tool-presets"] as const,
    lists: () => [...queryKeys.toolPresets.all, "list"] as const,
    detail: (id: string) => [...queryKeys.toolPresets.all, id] as const,
  },
} as const;

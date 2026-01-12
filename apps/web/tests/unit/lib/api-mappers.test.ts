/**
 * API mappers tests
 */

import {
  mapAgentDefinition,
  mapCheckpoint,
  mapMcpServerConfig,
  mapProject,
  mapSession,
  mapSkillDefinition,
  mapSlashCommand,
  mapToolPreset,
} from "@/lib/api-mappers";

describe("api-mappers", () => {
  it("converts session timestamps to Date instances", () => {
    const session = mapSession({
      id: "session-1",
      mode: "brainstorm",
      status: "active",
      created_at: "2026-01-11T10:00:00Z",
      updated_at: "2026-01-11T10:05:00Z",
      last_message_at: "2026-01-11T10:04:00Z",
      total_turns: 3,
      tags: [],
    });

    expect(session.created_at).toBeInstanceOf(Date);
    expect(session.updated_at).toBeInstanceOf(Date);
    expect(session.last_message_at).toBeInstanceOf(Date);
  });

  it("converts project timestamps to Date instances", () => {
    const project = mapProject({
      id: "project-1",
      name: "Demo",
      path: "demo",
      created_at: "2026-01-10T00:00:00Z",
      last_accessed_at: "2026-01-10T12:00:00Z",
      session_count: 2,
    });

    expect(project.created_at).toBeInstanceOf(Date);
    expect(project.last_accessed_at).toBeInstanceOf(Date);
  });

  it("maps agent, skill, and slash command dates", () => {
    const agent = mapAgentDefinition({
      id: "agent-1",
      name: "Reviewer",
      description: "Checks code",
      prompt: "Review code",
      created_at: "2026-01-11T00:00:00Z",
      updated_at: "2026-01-11T01:00:00Z",
    });

    const skill = mapSkillDefinition({
      id: "skill-1",
      name: "Skill",
      description: "Skill desc",
      content: "Content",
      enabled: true,
      created_at: "2026-01-11T00:00:00Z",
      updated_at: "2026-01-11T01:00:00Z",
    });

    const slash = mapSlashCommand({
      id: "cmd-1",
      name: "compact",
      description: "Compact output",
      content: "Rules",
      enabled: true,
      created_at: "2026-01-11T00:00:00Z",
      updated_at: "2026-01-11T01:00:00Z",
    });

    expect(agent.created_at).toBeInstanceOf(Date);
    expect(skill.updated_at).toBeInstanceOf(Date);
    expect(slash.created_at).toBeInstanceOf(Date);
  });

  it("maps tool presets and MCP servers", () => {
    const preset = mapToolPreset({
      id: "preset-1",
      name: "Default",
      tools: ["read_file"],
      created_at: "2026-01-11T00:00:00Z",
      is_default: true,
    });

    const server = mapMcpServerConfig({
      id: "server-1",
      name: "filesystem",
      type: "stdio",
      enabled: true,
      status: "active",
      created_at: "2026-01-11T00:00:00Z",
      updated_at: "2026-01-11T01:00:00Z",
    });

    expect(preset.created_at).toBeInstanceOf(Date);
    expect(preset.allowed_tools).toEqual(["read_file"]);
    expect(preset.is_system).toBe(true);
    expect(server.created_at).toBeInstanceOf(Date);
    expect(server.transport_type).toBe("stdio");
  });

  it("maps checkpoints with timestamps", () => {
    const checkpoint = mapCheckpoint({
      id: "checkpoint-1",
      session_id: "session-1",
      user_message_uuid: "uuid-1",
      created_at: "2026-01-11T02:00:00Z",
      files_modified: ["README.md"],
    });

    expect(checkpoint.created_at).toBeInstanceOf(Date);
  });
});

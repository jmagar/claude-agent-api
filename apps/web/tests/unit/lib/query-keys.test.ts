/**
 * Query key factory tests
 */

import { queryKeys } from "@/lib/query-keys";

describe("queryKeys", () => {
  it("builds session keys", () => {
    expect(queryKeys.sessions.all).toEqual(["sessions"]);
    expect(queryKeys.sessions.lists()).toEqual(["sessions", "list"]);
    expect(queryKeys.sessions.list("brainstorm")).toEqual([
      "sessions",
      "list",
      "brainstorm",
    ]);
    expect(queryKeys.sessions.details()).toEqual(["sessions", "detail"]);
    expect(queryKeys.sessions.detail("session-1")).toEqual([
      "sessions",
      "detail",
      "session-1",
    ]);
  });

  it("builds project keys", () => {
    expect(queryKeys.projects.all).toEqual(["projects"]);
    expect(queryKeys.projects.lists()).toEqual(["projects", "list"]);
    expect(queryKeys.projects.detail("project-1")).toEqual([
      "projects",
      "project-1",
    ]);
  });

  it("builds agent keys", () => {
    expect(queryKeys.agents.all).toEqual(["agents"]);
    expect(queryKeys.agents.lists()).toEqual(["agents", "list"]);
    expect(queryKeys.agents.detail("agent-1")).toEqual(["agents", "agent-1"]);
  });

  it("builds skill keys", () => {
    expect(queryKeys.skills.all).toEqual(["skills"]);
    expect(queryKeys.skills.lists()).toEqual(["skills", "list"]);
    expect(queryKeys.skills.detail("skill-1")).toEqual(["skills", "skill-1"]);
  });

  it("builds slash command keys", () => {
    expect(queryKeys.slashCommands.all).toEqual(["slash-commands"]);
    expect(queryKeys.slashCommands.lists()).toEqual([
      "slash-commands",
      "list",
    ]);
    expect(queryKeys.slashCommands.detail("cmd-1")).toEqual([
      "slash-commands",
      "cmd-1",
    ]);
  });

  it("builds MCP server keys", () => {
    expect(queryKeys.mcpServers.all).toEqual(["mcp-servers"]);
    expect(queryKeys.mcpServers.lists()).toEqual(["mcp-servers", "list"]);
    expect(queryKeys.mcpServers.detail("filesystem")).toEqual([
      "mcp-servers",
      "filesystem",
    ]);
    expect(queryKeys.mcpServers.tools("filesystem")).toEqual([
      "mcp-servers",
      "filesystem",
      "tools",
    ]);
  });

  it("builds tool preset keys", () => {
    expect(queryKeys.toolPresets.all).toEqual(["tool-presets"]);
    expect(queryKeys.toolPresets.lists()).toEqual(["tool-presets", "list"]);
    expect(queryKeys.toolPresets.detail("preset-1")).toEqual([
      "tool-presets",
      "preset-1",
    ]);
  });
});

/**
 * Tool Selection Utilities
 *
 * Provides helper functions for:
 * - Grouping tools by MCP server
 * - Filtering tools by search query and enabled state
 * - Calculating tool statistics
 *
 * Extracted from ToolManagementModal for reusability and clarity.
 */

import type { ToolDefinition } from "@/types";

/**
 * Groups tools by their MCP server name
 *
 * @param tools - Array of tool definitions
 * @returns Map of server name to tools array
 */
export function groupToolsByServer(
  tools: ToolDefinition[]
): Map<string, ToolDefinition[]> {
  const groups = new Map<string, ToolDefinition[]>();

  for (const tool of tools) {
    const serverName = tool.server ?? "unknown";
    const existing = groups.get(serverName) ?? [];
    existing.push(tool);
    groups.set(serverName, existing);
  }

  return groups;
}

/**
 * Filters tools based on search query and enabled state
 *
 * @param toolsByServer - Tools grouped by server
 * @param searchQuery - Search query string (case-insensitive)
 * @param showEnabledOnly - Whether to show only enabled tools
 * @returns Filtered map of server name to tools
 */
export function filterToolsByServer(
  toolsByServer: Map<string, ToolDefinition[]>,
  searchQuery: string,
  showEnabledOnly: boolean
): Map<string, ToolDefinition[]> {
  const filtered = new Map<string, ToolDefinition[]>();
  const query = searchQuery.toLowerCase().trim();

  for (const [serverName, serverTools] of toolsByServer) {
    const matchingTools = serverTools.filter((tool) => {
      const matchesSearch =
        !query ||
        tool.name.toLowerCase().includes(query) ||
        tool.description.toLowerCase().includes(query);
      const matchesEnabled = !showEnabledOnly || tool.enabled;
      return matchesSearch && matchesEnabled;
    });

    if (matchingTools.length > 0) {
      filtered.set(serverName, matchingTools);
    }
  }

  return filtered;
}

/**
 * Calculates the number of enabled tools
 *
 * @param tools - Array of tool definitions
 * @returns Count of enabled tools
 */
export function countEnabledTools(tools: ToolDefinition[]): number {
  return tools.filter((t) => t.enabled).length;
}

/**
 * Checks if all tools in a server are enabled
 *
 * @param serverTools - Tools for a specific server
 * @returns True if all tools are enabled
 */
export function areAllToolsEnabled(serverTools: ToolDefinition[]): boolean {
  return serverTools.every((t) => t.enabled);
}

/**
 * Checks if some (but not all) tools in a server are enabled
 *
 * @param serverTools - Tools for a specific server
 * @returns True if some tools are enabled
 */
export function areSomeToolsEnabled(serverTools: ToolDefinition[]): boolean {
  return serverTools.some((t) => t.enabled);
}

/**
 * Gets the list of enabled tool names
 *
 * @param tools - Array of tool definitions
 * @returns Array of enabled tool names
 */
export function getEnabledToolNames(tools: ToolDefinition[]): string[] {
  return tools.filter((t) => t.enabled).map((t) => t.name);
}

/**
 * Applies a preset's tool configuration
 *
 * @param tools - Current tools array
 * @param presetToolNames - Names of tools to enable from preset
 * @returns Array of tools with updated enabled state
 */
export function applyPresetToTools(
  tools: ToolDefinition[],
  presetToolNames: string[]
): ToolDefinition[] {
  const presetSet = new Set(presetToolNames);

  return tools.map((tool) => ({
    ...tool,
    enabled: presetSet.has(tool.name),
  }));
}

/**
 * Generates a batch of tool toggle operations for preset switching
 *
 * This optimizes preset switching by calculating all changes upfront
 * instead of toggling tools one by one.
 *
 * @param tools - Current tools array
 * @param presetToolNames - Names of tools to enable from preset
 * @returns Array of [toolName, enabled] tuples for batch update
 */
export function generatePresetToggleBatch(
  tools: ToolDefinition[],
  presetToolNames: string[]
): Array<[string, boolean]> {
  const presetSet = new Set(presetToolNames);
  const changes: Array<[string, boolean]> = [];

  for (const tool of tools) {
    const shouldBeEnabled = presetSet.has(tool.name);
    // Only include changes that differ from current state
    if (tool.enabled !== shouldBeEnabled) {
      changes.push([tool.name, shouldBeEnabled]);
    }
  }

  return changes;
}

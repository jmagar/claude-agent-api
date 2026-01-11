/**
 * Autocomplete API route (BFF)
 *
 * GET /api/autocomplete?trigger=@&query=code
 *
 * Returns autocomplete suggestions filtered by trigger type and search query.
 * Supports @ (mentions) and / (commands) triggers.
 *
 * Response:
 * {
 *   items: AutocompleteItem[]
 * }
 */

import { NextRequest, NextResponse } from "next/server";
import type { AutocompleteItem } from "@/types";
import { filterItems } from "@/lib/autocomplete-utils";

/**
 * Mock data for autocomplete suggestions
 * TODO: Replace with actual database/API queries
 */
const MOCK_AGENTS: AutocompleteItem[] = [
  {
    type: "agent",
    id: "agent-1",
    label: "code-reviewer",
    description: "Reviews code for best practices and potential issues",
    icon: "🤖",
    category: "Agents",
    recently_used: true,
    insert_text: "@code-reviewer",
  },
  {
    type: "agent",
    id: "agent-2",
    label: "test-runner",
    description: "Runs and analyzes test suites",
    icon: "🧪",
    category: "Agents",
    recently_used: false,
    insert_text: "@test-runner",
  },
];

const MOCK_MCP_SERVERS: AutocompleteItem[] = [
  {
    type: "mcp_server",
    id: "mcp-1",
    label: "postgres",
    description: "PostgreSQL database access",
    icon: "🐘",
    category: "MCP Servers",
    recently_used: false,
    insert_text: "@postgres",
  },
  {
    type: "mcp_server",
    id: "mcp-2",
    label: "browser",
    description: "Browser automation and web scraping",
    icon: "🌐",
    category: "MCP Servers",
    recently_used: false,
    insert_text: "@browser",
  },
];

const MOCK_FILES: AutocompleteItem[] = [
  {
    type: "file",
    id: "file-1",
    label: "README.md",
    description: "Project documentation",
    icon: "📄",
    category: "Files",
    recently_used: true,
    insert_text: "@README.md",
  },
  {
    type: "file",
    id: "file-2",
    label: "package.json",
    description: "NPM package configuration",
    icon: "📦",
    category: "Files",
    recently_used: false,
    insert_text: "@package.json",
  },
];

const MOCK_SKILLS: AutocompleteItem[] = [
  {
    type: "skill",
    id: "skill-1",
    label: "debugging",
    description: "Systematic debugging approach",
    icon: "🐛",
    category: "Skills",
    recently_used: false,
    insert_text: "/debugging",
  },
  {
    type: "skill",
    id: "skill-2",
    label: "refactoring",
    description: "Code refactoring best practices",
    icon: "♻️",
    category: "Skills",
    recently_used: false,
    insert_text: "/refactoring",
  },
];

const MOCK_SLASH_COMMANDS: AutocompleteItem[] = [
  {
    type: "slash_command",
    id: "cmd-1",
    label: "commit",
    description: "Create git commit with Claude",
    icon: "✅",
    category: "Commands",
    recently_used: false,
    insert_text: "/commit",
  },
  {
    type: "slash_command",
    id: "cmd-2",
    label: "compact",
    description: "Compact conversation history",
    icon: "🗜️",
    category: "Commands",
    recently_used: false,
    insert_text: "/compact",
  },
];

/**
 * Get all autocomplete items for @ trigger (mentions)
 */
function getMentionItems(): AutocompleteItem[] {
  return [...MOCK_AGENTS, ...MOCK_MCP_SERVERS, ...MOCK_FILES];
}

/**
 * Get all autocomplete items for / trigger (commands)
 */
function getCommandItems(): AutocompleteItem[] {
  return [...MOCK_SKILLS, ...MOCK_SLASH_COMMANDS];
}

/**
 * GET /api/autocomplete
 *
 * Query params:
 * - trigger: "@" or "/"
 * - query: search query (optional)
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const trigger = searchParams.get("trigger");
    const query = searchParams.get("query") || "";

    // Validate trigger
    if (!trigger || (trigger !== "@" && trigger !== "/")) {
      return NextResponse.json(
        { error: "Invalid trigger. Must be '@' or '/'" },
        { status: 400 }
      );
    }

    // Get items based on trigger
    const allItems =
      trigger === "@" ? getMentionItems() : getCommandItems();

    // Filter by search query
    const filteredItems = filterItems(allItems, query);

    return NextResponse.json({
      items: filteredItems,
    });
  } catch (error) {
    console.error("Autocomplete API error:", error);
    return NextResponse.json(
      { error: "Failed to fetch autocomplete suggestions" },
      { status: 500 }
    );
  }
}

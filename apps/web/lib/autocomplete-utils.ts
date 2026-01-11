/**
 * Autocomplete utility functions
 *
 * Shared utilities for trigger detection, filtering, sorting,
 * and entity type formatting used across autocomplete components.
 */

import type { AutocompleteItem } from "@/types";

/**
 * Result of trigger detection
 */
export interface TriggerDetectionResult {
  /** Trigger character found (@ or /) or null if none */
  trigger: "@" | "/" | null;
  /** Search query after the trigger */
  searchQuery: string;
  /** Index of trigger character in the text */
  triggerIndex: number;
}

/**
 * Detect trigger character and extract search query from input value
 *
 * Rules:
 * - @ trigger works anywhere in text
 * - / trigger only works at start of line or after space/newline
 * - No trigger if space found in search query (completed mention)
 * - Returns null trigger if no valid trigger found
 *
 * @param value - Full input text
 * @param cursorPosition - Current cursor position
 * @returns Trigger detection result with trigger, query, and index
 */
export function detectTrigger(
  value: string,
  cursorPosition: number
): TriggerDetectionResult {
  // Get text before cursor
  const textBeforeCursor = value.slice(0, cursorPosition);

  // Find last @ or / before cursor
  const atIndex = textBeforeCursor.lastIndexOf("@");
  const slashIndex = textBeforeCursor.lastIndexOf("/");

  // Determine which trigger is most recent
  const triggerIndex = Math.max(atIndex, slashIndex);

  if (triggerIndex === -1) {
    return { trigger: null, searchQuery: "", triggerIndex: -1 };
  }

  const trigger = triggerIndex === atIndex ? "@" : "/";

  // For slash commands, only trigger at start of line or after space
  if (trigger === "/" && triggerIndex > 0) {
    const charBeforeTrigger = value[triggerIndex - 1];
    if (charBeforeTrigger !== " " && charBeforeTrigger !== "\n") {
      return { trigger: null, searchQuery: "", triggerIndex: -1 };
    }
  }

  // Extract search query (text after trigger until cursor)
  const searchQuery = textBeforeCursor.slice(triggerIndex + 1);

  // Don't trigger if there's a space in the search query (completed mention)
  if (searchQuery.includes(" ")) {
    return { trigger: null, searchQuery: "", triggerIndex: -1 };
  }

  return { trigger, searchQuery, triggerIndex };
}

/**
 * Filter autocomplete items by search query
 *
 * Performs case-insensitive matching against item label and description.
 * Empty or whitespace-only queries return all items.
 *
 * @param items - Items to filter
 * @param query - Search query string
 * @returns Filtered items matching the query
 */
export function filterItems(
  items: AutocompleteItem[],
  query: string
): AutocompleteItem[] {
  if (!query || !query.trim()) {
    return items;
  }

  const lowerQuery = query.toLowerCase();
  return items.filter(
    (item) =>
      item.label.toLowerCase().includes(lowerQuery) ||
      item.description?.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Sort autocomplete items with recently used first
 *
 * Sorting order:
 * 1. Recently used items (recently_used: true)
 * 2. All other items
 * 3. Within each group, items maintain their original order
 *
 * @param items - Items to sort
 * @returns Sorted items with recently used first
 */
export function sortItems(items: AutocompleteItem[]): AutocompleteItem[] {
  return [...items].sort((a, b) => {
    // Recently used items come first
    if (a.recently_used && !b.recently_used) return -1;
    if (!a.recently_used && b.recently_used) return 1;
    return 0;
  });
}

/**
 * Group autocomplete items by category
 *
 * @param items - Items to group
 * @returns Map of category name to items in that category
 */
export function groupByCategory(
  items: AutocompleteItem[]
): Map<string, AutocompleteItem[]> {
  const grouped = new Map<string, AutocompleteItem[]>();

  for (const item of items) {
    const category = item.category || "Other";
    const categoryItems = grouped.get(category) || [];
    categoryItems.push(item);
    grouped.set(category, categoryItems);
  }

  return grouped;
}

/**
 * Format entity type for display
 *
 * Converts internal entity type to human-readable badge text.
 *
 * @param type - Entity type from AutocompleteItem
 * @returns Formatted display string
 */
export function formatEntityType(
  type: AutocompleteItem["type"]
): string {
  switch (type) {
    case "agent":
      return "Agent";
    case "mcp_server":
      return "MCP";
    case "file":
      return "File";
    case "skill":
      return "Skill";
    case "slash_command":
      return "Command";
    default:
      return "Item";
  }
}

/**
 * Get color classes for entity type badge
 *
 * Returns Tailwind CSS classes for consistent badge styling.
 *
 * @param type - Entity type from AutocompleteItem
 * @returns Tailwind CSS class string for badge styling
 */
export function getEntityTypeBadgeColor(
  type: AutocompleteItem["type"]
): string {
  switch (type) {
    case "agent":
      return "bg-purple-100 text-purple-700";
    case "mcp_server":
      return "bg-blue-100 text-blue-700";
    case "file":
      return "bg-green-100 text-green-700";
    case "skill":
      return "bg-orange-100 text-orange-700";
    case "slash_command":
      return "bg-gray-100 text-gray-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
}

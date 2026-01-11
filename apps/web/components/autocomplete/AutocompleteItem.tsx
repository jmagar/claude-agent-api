/**
 * AutocompleteItem component
 *
 * Individual autocomplete item displaying icon, label, description, type badge,
 * and recently used indicator. Supports selection via click or keyboard.
 *
 * @see tests/unit/components/AutocompleteItem.test.tsx for test specifications
 */

"use client";

import type { AutocompleteItem as AutocompleteItemType } from "@/types";
import { cn } from "@/lib/utils";
import {
  formatEntityType,
  getEntityTypeBadgeColor,
} from "@/lib/autocomplete-utils";

export interface AutocompleteItemProps {
  /** Autocomplete item data */
  item: AutocompleteItemType;
  /** Callback when item is selected */
  onSelect: (item: AutocompleteItemType) => void;
  /** Whether this item is currently selected via keyboard navigation */
  isSelected?: boolean;
  /** Whether to show category label */
  showCategory?: boolean;
  /** Optional custom className */
  className?: string;
}

/**
 * Get trigger prefix based on insert text
 */
function getTriggerPrefix(insertText: string): string {
  if (insertText.startsWith("/")) {
    return "/";
  }
  if (insertText.startsWith("@")) {
    return "@";
  }
  return "";
}

export function AutocompleteItem({
  item,
  onSelect,
  isSelected = false,
  showCategory = false,
  className,
}: AutocompleteItemProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onSelect(item);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(item);
    }
  };

  const triggerPrefix = getTriggerPrefix(item.insert_text);

  return (
    <button
      role="button"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      data-selected={isSelected ? "true" : undefined}
      aria-label={`Select ${item.label}`}
      className={cn(
        "flex w-full items-start gap-12 rounded-6 px-12 py-8 text-left transition-colors",
        "hover:bg-gray-100 focus:outline-none",
        isSelected && "bg-gray-100 selected highlight active",
        className
      )}
    >
      {/* Icon */}
      {item.icon && (
        <span className="flex-shrink-0 text-20" aria-hidden="true">
          {item.icon}
        </span>
      )}

      {/* Content */}
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        {/* Label row */}
        <div className="flex items-center gap-8">
          {/* Trigger prefix hint */}
          {triggerPrefix && (
            <span className="text-12 text-gray-500" aria-hidden="true">
              {triggerPrefix}
            </span>
          )}

          {/* Label */}
          <span
            data-testid="label"
            className="overflow-hidden text-ellipsis whitespace-nowrap text-14 font-medium text-gray-900"
          >
            {item.label}
          </span>

          {/* Recently used indicator */}
          {item.recently_used && (
            <span
              className="ml-auto flex-shrink-0 text-12 text-gray-500"
              aria-label="Recently used"
              title="Recently used"
            >
              ⭐
            </span>
          )}
        </div>

        {/* Description */}
        {item.description && (
          <p
            data-testid="description"
            className="overflow-hidden text-ellipsis whitespace-nowrap text-12 text-gray-600"
          >
            {item.description}
          </p>
        )}

        {/* Category and type badge row */}
        <div className="flex items-center gap-8">
          {/* Category */}
          {showCategory && item.category && (
            <span className="text-10 text-gray-500">{item.category}</span>
          )}

          {/* Entity type badge */}
          <span
            className={cn(
              "rounded-4 px-6 py-2 text-10",
              getEntityTypeBadgeColor(item.type)
            )}
          >
            {formatEntityType(item.type)}
          </span>
        </div>
      </div>
    </button>
  );
}

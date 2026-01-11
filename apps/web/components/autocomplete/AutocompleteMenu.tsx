/**
 * AutocompleteMenu component
 *
 * Dropdown menu displaying autocomplete suggestions with keyboard navigation,
 * filtering, recently used items, and category grouping.
 *
 * @see tests/unit/components/AutocompleteMenu.test.tsx for test specifications
 */

"use client";

import { useEffect, useRef, useState } from "react";
import type { AutocompleteItem as AutocompleteItemType } from "@/types";
import { AutocompleteItem } from "./AutocompleteItem";
import { cn } from "@/lib/utils";
import {
  filterItems,
  sortItems,
  groupByCategory as groupItemsByCategory,
} from "@/lib/autocomplete-utils";

export interface AutocompleteMenuProps {
  /** Autocomplete items to display */
  items: AutocompleteItemType[];
  /** Callback when item is selected */
  onSelect: (item: AutocompleteItemType) => void;
  /** Optional callback when menu should close (Escape key) */
  onClose?: () => void;
  /** Optional search query for client-side filtering */
  searchQuery?: string;
  /** Whether to group items by category */
  groupByCategory?: boolean;
  /** Position for the menu (absolute) */
  position?: { top: number; left: number };
  /** Whether data is loading */
  isLoading?: boolean;
  /** Error message if loading failed */
  error?: string;
  /** Optional custom className */
  className?: string;
}

export function AutocompleteMenu({
  items,
  onSelect,
  onClose,
  searchQuery,
  groupByCategory = false,
  position,
  isLoading = false,
  error,
  className,
}: AutocompleteMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  // Filter and sort items
  const filteredItems = filterItems(items, searchQuery || "");
  const sortedItems = sortItems(filteredItems);

  // Reset selected index when items change
  useEffect(() => {
    setSelectedIndex(-1);
  }, [items, searchQuery]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (sortedItems.length === 0) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % sortedItems.length);
          break;

        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => {
            // If no item selected or at first item, wrap to last item
            if (prev <= 0) {
              return sortedItems.length - 1;
            }
            return prev - 1;
          });
          break;

        case "Enter":
          e.preventDefault();
          if (selectedIndex >= 0 && selectedIndex < sortedItems.length) {
            onSelect(sortedItems[selectedIndex]);
          }
          break;

        case "Escape":
          e.preventDefault();
          onClose?.();
          break;

        default:
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [sortedItems, selectedIndex, onSelect, onClose]);

  // Loading state
  if (isLoading) {
    return (
      <div
        ref={menuRef}
        role="menu"
        tabIndex={-1}
        style={position}
        className={cn(
          "absolute z-50 w-400 max-h-300 overflow-y-auto",
          "rounded-8 border border-gray-300 bg-white shadow-lg",
          "py-8",
          className
        )}
      >
        <div className="px-12 py-16 text-center text-14 text-gray-600">
          Loading...
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div
        ref={menuRef}
        role="menu"
        tabIndex={-1}
        style={position}
        className={cn(
          "absolute z-50 w-400 max-h-300 overflow-y-auto",
          "rounded-8 border border-gray-300 bg-white shadow-lg",
          "py-8",
          className
        )}
      >
        <div className="px-12 py-16 text-center text-14 text-red-600">
          {error}
        </div>
      </div>
    );
  }

  // Empty state - no items or no results after filtering
  if (items.length === 0 || sortedItems.length === 0) {
    const message = searchQuery && searchQuery.trim()
      ? `No results found for "${searchQuery}"`
      : "No suggestions available";

    return (
      <div
        ref={menuRef}
        role="menu"
        tabIndex={-1}
        style={position}
        className={cn(
          "absolute z-50 w-400 max-h-300 overflow-y-auto",
          "rounded-8 border border-gray-300 bg-white shadow-lg",
          "py-8",
          className
        )}
      >
        <div className="px-12 py-16 text-center text-14 text-gray-600">
          {message}
        </div>
      </div>
    );
  }

  // Render grouped or ungrouped items
  const renderItems = () => {
    if (groupByCategory) {
      const grouped = groupItemsByCategory(sortedItems);
      const categories = Array.from(grouped.keys()).sort();

      return categories.map((category) => (
        <div key={category} className="mb-8">
          {/* Category header */}
          <div className="px-12 py-6 text-10 font-semibold uppercase text-gray-500">
            {category}
          </div>

          {/* Items in category */}
          {(grouped.get(category) || []).map((item) => {
            const itemIndex = sortedItems.indexOf(item);
            return (
              <AutocompleteItem
                key={item.id}
                item={item}
                onSelect={onSelect}
                isSelected={selectedIndex === itemIndex}
              />
            );
          })}
        </div>
      ));
    }

    // Ungrouped items
    return sortedItems.map((item, index) => (
      <AutocompleteItem
        key={item.id}
        item={item}
        onSelect={onSelect}
        isSelected={selectedIndex === index}
      />
    ));
  };

  return (
    <div
      ref={menuRef}
      role="menu"
      tabIndex={-1}
      style={position}
      className={cn(
        "absolute z-50 w-400 max-h-300 overflow-y-auto",
        "rounded-8 border border-gray-300 bg-white shadow-lg",
        "py-4",
        className
      )}
    >
      {renderItems()}
    </div>
  );
}

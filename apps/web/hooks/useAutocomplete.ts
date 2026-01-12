/**
 * useAutocomplete hook
 *
 * Hook for fetching autocomplete suggestions with debouncing, filtering,
 * and error handling. Supports @ (mentions) and / (commands) triggers.
 *
 * Features:
 * - Debounced API calls (300ms)
 * - Automatic trigger detection (@ or /)
 * - Loading and error states
 * - Client-side filtering
 */

import { useState, useEffect, useCallback, useRef } from "react";
import type { AutocompleteItem } from "@/types";
import { detectTrigger } from "@/lib/autocomplete-utils";

export interface UseAutocompleteOptions {
  /** Current input value */
  value: string;
  /** Cursor position in input */
  cursorPosition: number;
  /** API endpoint for fetching suggestions */
  apiUrl?: string;
  /** Debounce delay in milliseconds (default: 300) */
  debounceMs?: number;
  /** Whether autocomplete is enabled */
  enabled?: boolean;
}

export interface UseAutocompleteResult {
  /** Filtered autocomplete items */
  items: AutocompleteItem[];
  /** Whether data is loading */
  isLoading: boolean;
  /** Error message if loading failed */
  error: string | null;
  /** Whether autocomplete menu should be shown */
  isOpen: boolean;
  /** Current trigger character (@ or /) */
  trigger: "@" | "/" | null;
  /** Search query after trigger */
  searchQuery: string;
  /** Close the autocomplete menu */
  close: () => void;
  /** Select an item and insert into input */
  selectItem: (item: AutocompleteItem) => {
    value: string;
    cursorPosition: number;
  };
}

/**
 * Fetch autocomplete suggestions from API
 */
async function fetchSuggestions(
  trigger: "@" | "/",
  searchQuery: string,
  apiUrl: string,
  signal: AbortSignal
): Promise<AutocompleteItem[]> {
  const params = new URLSearchParams({
    trigger,
    query: searchQuery,
  });

  const response = await fetch(`${apiUrl}?${params}`, {
    method: "GET",
    signal,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch suggestions: ${response.statusText}`);
  }

  const data = await response.json();
  return data.items || [];
}

export function useAutocomplete({
  value,
  cursorPosition,
  apiUrl = "/api/autocomplete",
  debounceMs = 300,
  enabled = true,
}: UseAutocompleteOptions): UseAutocompleteResult {
  const [items, setItems] = useState<AutocompleteItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Detect trigger and search query
  const { trigger, searchQuery, triggerIndex } = detectTrigger(
    value,
    cursorPosition
  );

  // Fetch suggestions when trigger/query changes (debounced)
  useEffect(() => {
    if (!enabled || !trigger) {
      setIsOpen(false);
      setItems([]);
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear previous debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set loading state immediately
    setIsLoading(true);
    setError(null);
    setIsOpen(true);

    // Debounce API call
    debounceTimerRef.current = setTimeout(async () => {
      try {
        const controller = new AbortController();
        abortControllerRef.current = controller;

        const suggestions = await fetchSuggestions(
          trigger,
          searchQuery,
          apiUrl,
          controller.signal
        );

        // Only update if not aborted
        if (!controller.signal.aborted) {
          setItems(suggestions);
          setIsLoading(false);
        }
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          setError(err.message || "Failed to load suggestions");
          setIsLoading(false);
        }
      }
    }, debounceMs);

    // Cleanup
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [trigger, searchQuery, apiUrl, debounceMs, enabled]);

  // Close autocomplete menu
  const close = useCallback(() => {
    setIsOpen(false);
    setItems([]);
    setError(null);
  }, []);

  // Select item and insert into input
  const selectItem = useCallback(
    (item: AutocompleteItem): { value: string; cursorPosition: number } => {
      if (triggerIndex === -1) {
        return { value, cursorPosition };
      }

      // Replace trigger + search query with insert_text
      const before = value.slice(0, triggerIndex);
      const after = value.slice(cursorPosition);
      const newValue = `${before}${item.insert_text} ${after}`;
      const newCursorPosition = before.length + item.insert_text.length + 1;

      close();
      return { value: newValue, cursorPosition: newCursorPosition };
    },
    [value, triggerIndex, cursorPosition, close]
  );

  return {
    items,
    isLoading,
    error,
    isOpen,
    trigger,
    searchQuery,
    close,
    selectItem,
  };
}

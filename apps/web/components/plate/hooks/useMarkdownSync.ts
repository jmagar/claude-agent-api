/**
 * useMarkdownSync Hook
 *
 * Bidirectional sync between markdown string and Slate JSON.
 * Converts markdown to Slate on mount, syncs Slate changes back to markdown.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  markdownToSlate,
  slateToMarkdown,
  type SlateValue,
} from '@/lib/slate-serializers';

export interface UseMarkdownSyncReturn {
  slateValue: SlateValue;
  handleSlateChange: (newValue: SlateValue) => void;
}

/**
 * Hook for syncing markdown and Slate editor state
 *
 * @param markdownValue - Current markdown string
 * @param onMarkdownChange - Callback when markdown changes
 * @returns Slate value and change handler
 */
export function useMarkdownSync(
  markdownValue: string,
  onMarkdownChange: (value: string) => void
): UseMarkdownSyncReturn {
  // Convert markdown to Slate on mount or when markdownValue changes externally
  const [slateValue, setSlateValue] = useState<SlateValue>(() =>
    markdownToSlate(markdownValue)
  );

  // Track if this is the first render to avoid infinite loops
  const [isInitialized, setIsInitialized] = useState(false);

  // Update Slate value when markdown value changes externally
  useEffect(() => {
    if (!isInitialized) {
      setIsInitialized(true);
      return;
    }

    // Only update if the markdown value changed externally
    // (not from our own Slate changes)
    const currentMarkdown = slateToMarkdown(slateValue);
    if (currentMarkdown.trim() !== markdownValue.trim()) {
      setSlateValue(markdownToSlate(markdownValue));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally only sync when markdownValue changes externally.
    // Including slateValue would cause infinite re-render loops since we're comparing it.
    // isInitialized is only read, not written after initialization flag is set.
  }, [markdownValue]);

  // Handle Slate changes and convert back to markdown
  const handleSlateChange = useCallback(
    (newValue: SlateValue) => {
      setSlateValue(newValue);
      const newMarkdown = slateToMarkdown(newValue);
      onMarkdownChange(newMarkdown);
    },
    [onMarkdownChange]
  );

  return {
    slateValue,
    handleSlateChange,
  };
}

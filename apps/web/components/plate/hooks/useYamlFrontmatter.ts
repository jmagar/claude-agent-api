/**
 * useYamlFrontmatter Hook
 *
 * Manages YAML frontmatter and content body separately.
 * Integrates with yaml-validation.ts utilities for parsing and serialization.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  parseYamlFrontmatter,
  serializeYamlFrontmatter,
} from '@/lib/yaml-validation';

export interface UseYamlFrontmatterReturn {
  frontmatter: Record<string, unknown>;
  body: string;
  updateFrontmatter: (data: Record<string, unknown>) => void;
  updateBody: (content: string) => void;
}

/**
 * Hook for managing YAML frontmatter and content body
 *
 * @param value - Full content with YAML frontmatter
 * @param onChange - Callback when content changes
 * @returns Frontmatter, body, and update functions
 */
export function useYamlFrontmatter(
  value: string,
  onChange: (value: string) => void
): UseYamlFrontmatterReturn {
  // Parse frontmatter and body on mount or when value changes externally
  const [frontmatter, setFrontmatter] = useState<Record<string, unknown>>(() => {
    const parsed = parseYamlFrontmatter(value);
    return parsed.data as Record<string, unknown>;
  });

  const [body, setBody] = useState<string>(() => {
    const parsed = parseYamlFrontmatter(value);
    return parsed.content;
  });

  // Track if this is the first render to avoid infinite loops
  const [isInitialized, setIsInitialized] = useState(false);

  // Update state when value changes externally
  useEffect(() => {
    if (!isInitialized) {
      setIsInitialized(true);
      return;
    }

    const parsed = parseYamlFrontmatter(value);
    setFrontmatter(parsed.data as Record<string, unknown>);
    setBody(parsed.content);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Intentionally only sync when value changes externally
  }, [value]);

  // Update frontmatter and serialize back to markdown
  const updateFrontmatter = useCallback(
    (newData: Record<string, unknown>) => {
      const mergedData = { ...frontmatter, ...newData };
      setFrontmatter(mergedData);
      const serialized = serializeYamlFrontmatter(mergedData, body);
      onChange(serialized);
    },
    [frontmatter, body, onChange]
  );

  // Update body and serialize back to markdown
  const updateBody = useCallback(
    (newBody: string) => {
      setBody(newBody);
      const serialized = serializeYamlFrontmatter(frontmatter, newBody);
      onChange(serialized);
    },
    [frontmatter, onChange]
  );

  return {
    frontmatter,
    body,
    updateFrontmatter,
    updateBody,
  };
}

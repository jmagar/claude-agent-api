/**
 * ThinkingBlock component
 *
 * Displays collapsible thinking content from Claude's internal reasoning.
 * Collapsed by default to reduce visual clutter.
 *
 * Features:
 * - Collapsed by default
 * - Click to expand/collapse
 * - Shows preview of first line when collapsed
 * - Full content when expanded
 */

"use client";

import { useState, memo } from "react";
import { ChevronDown, ChevronRight, Brain } from "lucide-react";

export interface ThinkingBlockProps {
  thinking: string;
  collapsed?: boolean;
  onToggle?: () => void;
}

export const ThinkingBlock = memo(function ThinkingBlock({
  thinking,
  collapsed: externalCollapsed,
  onToggle,
}: ThinkingBlockProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(true);

  // Use external collapse state if provided, otherwise use internal
  const isCollapsed = externalCollapsed !== undefined ? externalCollapsed : internalCollapsed;

  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalCollapsed(!internalCollapsed);
    }
  };

  // Get first line for preview
  const getPreview = () => {
    const firstLine = thinking.split("\n")[0];
    if (firstLine.length > 80) {
      return firstLine.substring(0, 80) + "...";
    }
    return firstLine;
  };

  return (
    <div
      data-testid="thinking-block"
      className="border border-purple-200 rounded-md bg-purple-50/50"
      aria-expanded={!isCollapsed}
    >
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-16 py-12 hover:bg-purple-100/50 transition-colors"
      >
        <div className="flex items-center gap-12">
          {isCollapsed ? (
            <ChevronRight className="w-16 h-16 text-purple-400" />
          ) : (
            <ChevronDown className="w-16 h-16 text-purple-400" />
          )}
          <Brain className="w-16 h-16 text-purple-600" />
          <span className="text-12 font-medium text-purple-900">Thinking</span>
          {isCollapsed && (
            <span className="text-12 text-purple-700 italic">{getPreview()}</span>
          )}
        </div>
      </button>

      {/* Content (expanded) */}
      <div
        className={`px-16 pb-12 border-t border-purple-100 ${
          isCollapsed ? "hidden" : "block"
        }`}
      >
        <pre className="mt-12 text-12 text-purple-900 whitespace-pre-wrap font-sans">
          {thinking}
        </pre>
      </div>
    </div>
  );
});

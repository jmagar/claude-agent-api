/**
 * SubagentCard component
 *
 * Displays a collapsible card for subagent activities with:
 * - Subagent type and status badge
 * - Collapsed by default to reduce visual clutter
 * - Child tool calls nested within
 * - Progress indication for running subagents
 * - Duration and token usage display
 */

"use client";

import { useState, memo, useEffect, type ReactNode } from "react";
import type { ToolCall, ToolStatus } from "@/types";
import { ChevronDown, ChevronRight, Bot, Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

export interface SubagentCardProps {
  /** Unique identifier for the subagent */
  id: string;
  /** Type or name of the subagent (e.g., "Explore", "Plan", "Bash") */
  type: string;
  /** Current status of the subagent */
  status: ToolStatus;
  /** Description or prompt given to the subagent */
  description?: string;
  /** Child tool calls made by this subagent */
  childToolCalls?: ToolCall[];
  /** Whether the card is collapsed */
  collapsed?: boolean;
  /** Callback when collapse state toggles */
  onToggle?: () => void;
  /** Duration in milliseconds */
  duration_ms?: number;
  /** Token usage for this subagent */
  tokenUsage?: {
    input: number;
    output: number;
  };
  /** Children to render inside the card when expanded */
  children?: ReactNode;
}

export const SubagentCard = memo(function SubagentCard({
  id,
  type,
  status,
  description,
  childToolCalls = [],
  collapsed: externalCollapsed,
  onToggle,
  duration_ms,
  tokenUsage,
  children,
}: SubagentCardProps) {
  // Default to collapsed for subagents
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

  // Auto-expand on completion or error
  useEffect(() => {
    if (externalCollapsed !== undefined) {
      return;
    }
    if (status === "error") {
      setInternalCollapsed(false);
    }
  }, [status, externalCollapsed]);

  const getStatusColor = (s: ToolStatus) => {
    switch (s) {
      case "success":
        return "text-emerald-600 bg-emerald-50 border-emerald-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      case "running":
        return "text-indigo-600 bg-indigo-50 border-indigo-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getStatusIcon = (s: ToolStatus) => {
    switch (s) {
      case "success":
        return <CheckCircle className="w-14 h-14 text-emerald-500" />;
      case "error":
        return <XCircle className="w-14 h-14 text-red-500" />;
      case "running":
        return <Loader2 className="w-14 h-14 animate-spin text-indigo-500" role="status" />;
      default:
        return <Clock className="w-14 h-14 text-gray-400" />;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return null;
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatTokens = (usage?: { input: number; output: number }) => {
    if (!usage) return null;
    const total = usage.input + usage.output;
    if (total < 1000) return `${total} tokens`;
    return `${(total / 1000).toFixed(1)}k tokens`;
  };

  const activeToolCount = childToolCalls.filter((t) => t.status === "running").length;
  const completedToolCount = childToolCalls.filter((t) => t.status === "success").length;
  const totalToolCount = childToolCalls.length;

  return (
    <div
      data-testid={`subagent-${id}`}
      className="border border-indigo-200 rounded-md bg-indigo-50/30 shadow-sm"
    >
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-16 py-12 hover:bg-indigo-100/50 transition-colors"
        aria-expanded={!isCollapsed}
      >
        <div className="flex items-center gap-12">
          {isCollapsed ? (
            <ChevronRight className="w-16 h-16 text-indigo-400" />
          ) : (
            <ChevronDown className="w-16 h-16 text-indigo-400" />
          )}
          <Bot className="w-16 h-16 text-indigo-600" />
          <span className="font-medium text-14 text-indigo-900">{type}</span>
          <span
            className={`px-8 py-2 text-12 rounded-full border ${getStatusColor(status)}`}
          >
            {status}
          </span>
          {totalToolCount > 0 && (
            <span className="text-12 text-indigo-600">
              {activeToolCount > 0
                ? `${completedToolCount}/${totalToolCount} tools`
                : `${totalToolCount} tools`}
            </span>
          )}
          {duration_ms && (
            <span className="text-12 text-indigo-500">
              {formatDuration(duration_ms)}
            </span>
          )}
          {tokenUsage && (
            <span className="text-12 text-indigo-400">
              {formatTokens(tokenUsage)}
            </span>
          )}
        </div>

        {getStatusIcon(status)}
      </button>

      {/* Body (expanded) */}
      {!isCollapsed && (
        <div className="px-16 pb-12 border-t border-indigo-100">
          {/* Description */}
          {description && (
            <div className="mt-12">
              <p className="text-12 text-indigo-800 italic">&quot;{description}&quot;</p>
            </div>
          )}

          {/* Children (tool calls or custom content) */}
          {children && <div className="mt-12 space-y-8">{children}</div>}

          {/* Progress bar for running subagents */}
          {status === "running" && totalToolCount > 0 && (
            <div className="mt-12">
              <div className="flex justify-between text-12 text-indigo-600 mb-4">
                <span>Progress</span>
                <span>
                  {completedToolCount}/{totalToolCount}
                </span>
              </div>
              <div className="h-4 bg-indigo-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-500 transition-all duration-300"
                  style={{
                    width: `${totalToolCount > 0 ? (completedToolCount / totalToolCount) * 100 : 0}%`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

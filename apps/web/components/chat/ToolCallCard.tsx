/**
 * ToolCallCard component
 *
 * Displays a collapsible card for tool calls with:
 * - Tool name and status badge
 * - Collapsible input/output sections
 * - Retry button for failed tools
 * - Approval/deny buttons for pending tools
 * - Duration display after completion
 * - JSON syntax highlighting for structured data
 */

"use client";

import { useState, memo, useEffect } from "react";
import type { ToolCall } from "@/types";
import { ChevronDown, ChevronRight, RefreshCw, Check, X, Loader2 } from "lucide-react";
import { CodeBlock, formatCodeValue } from "@/components/ui/CodeBlock";

export interface ToolCallCardProps {
  toolCall: ToolCall;
  collapsed?: boolean;
  onToggle?: () => void;
  onRetry?: () => void;
  onApprove?: () => void;
  onDeny?: () => void;
  needsApproval?: boolean;
}

export const ToolCallCard = memo(function ToolCallCard({
  toolCall,
  collapsed: externalCollapsed,
  onToggle,
  onRetry,
  onApprove,
  onDeny,
  needsApproval = false,
}: ToolCallCardProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(
    toolCall.status !== "success" && toolCall.status !== "error"
  );

  // Use external collapse state if provided, otherwise use internal
  const isCollapsed = externalCollapsed !== undefined ? externalCollapsed : internalCollapsed;

  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalCollapsed(!internalCollapsed);
    }
  };

  useEffect(() => {
    if (externalCollapsed !== undefined) {
      return;
    }
    if (toolCall.status === "success" || toolCall.status === "error") {
      setInternalCollapsed(false);
    }
  }, [toolCall.status, externalCollapsed]);

  const getStatusColor = (status: ToolCall["status"]) => {
    switch (status) {
      case "success":
        return "text-green-600 bg-green-50 border-green-200";
      case "error":
        return "text-red-600 bg-red-50 border-red-200";
      case "running":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return null;
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div
      data-testid={`tool-call-${toolCall.id}`}
      className="border border-gray-200 rounded-md bg-white shadow-sm"
    >
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-16 py-12 hover:bg-gray-50 transition-colors"
        aria-expanded={!isCollapsed}
      >
        <div className="flex items-center gap-12">
          {isCollapsed ? (
            <ChevronRight className="w-16 h-16 text-gray-400" />
          ) : (
            <ChevronDown className="w-16 h-16 text-gray-400" />
          )}
          <span className="font-medium text-14">{toolCall.name}</span>
          <span
            className={`px-8 py-2 text-12 rounded-full border ${getStatusColor(
              toolCall.status
            )}`}
          >
            {toolCall.status}
          </span>
          {toolCall.duration_ms && (
            <span className="text-12 text-gray-500">
              {formatDuration(toolCall.duration_ms)}
            </span>
          )}
        </div>

        {toolCall.status === "running" && (
          <Loader2 className="w-16 h-16 animate-spin text-blue-500" role="status" />
        )}
      </button>

      {/* Body (expanded) */}
      {!isCollapsed && (
        <div className="px-16 pb-12 border-t border-gray-100">
          {/* Input */}
          <div className="mt-12">
            <h4 className="text-12 font-medium text-gray-700 mb-4">Input</h4>
            <CodeBlock
              code={formatCodeValue(toolCall.input)}
              language="json"
              className="overflow-x-auto"
            />
          </div>

          {/* Output or Error */}
          {toolCall.output && (
            <div className="mt-12">
              <h4 className="text-12 font-medium text-gray-700 mb-4">Output</h4>
              <CodeBlock
                code={formatCodeValue(toolCall.output)}
                language="json"
                className="overflow-x-auto"
              />
            </div>
          )}

          {toolCall.error && (
            <div className="mt-12">
              <h4 className="text-12 font-medium text-red-700 mb-4">Error</h4>
              <pre className="bg-red-50 p-8 rounded text-12 overflow-x-auto text-red-700">
                <code>{toolCall.error}</code>
              </pre>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-12 flex gap-8">
            {toolCall.status === "error" && onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-6 px-12 py-6 text-12 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                aria-label="Retry tool execution"
              >
                <RefreshCw className="w-14 h-14" />
                Retry
              </button>
            )}

            {needsApproval && (
              <>
                {onApprove && (
                  <button
                    onClick={onApprove}
                    className="flex items-center gap-6 px-12 py-6 text-12 bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
                    aria-label="Approve tool execution"
                  >
                    <Check className="w-14 h-14" />
                    Approve
                  </button>
                )}

                {onDeny && (
                  <button
                    onClick={onDeny}
                    className="flex items-center gap-6 px-12 py-6 text-12 bg-red-50 text-red-700 rounded hover:bg-red-100 transition-colors"
                    aria-label="Deny tool execution"
                  >
                    <X className="w-14 h-14" />
                    Deny
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
});

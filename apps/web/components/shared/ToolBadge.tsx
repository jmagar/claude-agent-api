/**
 * ToolBadge Component
 *
 * Displays the count of active/enabled tools with a clickable badge.
 * Clicking opens the tool management modal.
 *
 * @see FR-016: System MUST show tool count badge in composer
 */

"use client";

import { memo } from "react";
import { Wrench } from "lucide-react";

export interface ToolBadgeProps {
  /** Number of enabled tools */
  count: number;
  /** Total number of available tools */
  total?: number;
  /** Click handler to open tool management */
  onClick?: () => void;
  /** Whether the badge is disabled */
  disabled?: boolean;
  /** Size variant */
  size?: "sm" | "md" | "lg";
}

export const ToolBadge = memo(function ToolBadge({
  count,
  total,
  onClick,
  disabled = false,
  size = "md",
}: ToolBadgeProps) {
  const sizeClasses = {
    sm: "text-12 px-6 py-2 gap-4",
    md: "text-14 px-8 py-4 gap-6",
    lg: "text-16 px-10 py-6 gap-8",
  };

  const iconSizes = {
    sm: "h-12 w-12",
    md: "h-14 w-14",
    lg: "h-16 w-16",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-testid="tool-badge"
      aria-label={`${count} tools enabled${total ? ` of ${total} total` : ""}`}
      className={`
        inline-flex items-center rounded-full
        bg-gray-100 text-gray-700
        transition-colors
        hover:bg-gray-200
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        disabled:cursor-not-allowed disabled:opacity-50
        ${sizeClasses[size]}
      `}
    >
      <Wrench className={iconSizes[size]} aria-hidden="true" />
      <span className="font-medium">{count}</span>
      {total !== undefined && (
        <span className="text-gray-500">/ {total}</span>
      )}
    </button>
  );
});

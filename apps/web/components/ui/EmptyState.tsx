/**
 * EmptyState component
 *
 * Displays friendly empty state messages with icon, title, description, and optional CTAs.
 * Used across the app for no sessions, no search results, no MCP servers, etc.
 *
 * @see wireframes/10-loading-empty-states.html for design spec
 */

import { ReactNode } from "react";

export interface EmptyStateProps {
  /** Icon (emoji or icon component) - displayed at 64px with 0.3 opacity */
  icon: ReactNode;
  /** Title text - 18px, font-weight 600 */
  title: string;
  /** Description text - 14px, #666, max-width 400px */
  description: string;
  /** Primary action button text */
  primaryAction?: string;
  /** Primary action click handler */
  onPrimaryAction?: () => void;
  /** Secondary action button text */
  secondaryAction?: string;
  /** Secondary action click handler */
  onSecondaryAction?: () => void;
  /** Additional content below actions */
  children?: ReactNode;
}

export function EmptyState({
  icon,
  title,
  description,
  primaryAction,
  onPrimaryAction,
  secondaryAction,
  onSecondaryAction,
  children,
}: EmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-20 py-40 text-center">
      {/* Icon */}
      <div className="mb-16 text-64 opacity-30">{icon}</div>

      {/* Title */}
      <h2 className="mb-8 text-18 font-semibold text-gray-700">{title}</h2>

      {/* Description */}
      <p className="mb-20 max-w-[400px] text-14 leading-relaxed text-gray-600">
        {description}
      </p>

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="flex gap-8">
          {primaryAction && (
            <button
              onClick={onPrimaryAction}
              className="rounded-6 bg-gray-700 px-20 py-10 text-14 font-medium text-white hover:bg-gray-600"
            >
              {primaryAction}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={onSecondaryAction}
              className="rounded-6 border border-gray-300 bg-white px-20 py-10 text-14 font-medium text-gray-700 hover:bg-gray-50"
            >
              {secondaryAction}
            </button>
          )}
        </div>
      )}

      {/* Additional content */}
      {children && <div className="mt-16">{children}</div>}
    </div>
  );
}

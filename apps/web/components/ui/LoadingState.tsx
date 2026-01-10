/**
 * LoadingState component
 *
 * Provides loading indicators in two variants:
 * 1. Skeleton: Animated shimmer placeholders for predictable content (lists, messages)
 * 2. Spinner: Circular loading indicator for indeterminate loading (initial load)
 *
 * @see wireframes/10-loading-empty-states.html for design spec
 */

import { ReactNode } from "react";

/** Skeleton loading placeholder with animated shimmer */
export interface SkeletonProps {
  /** Height of skeleton in pixels or CSS value */
  height?: string | number;
  /** Width of skeleton (default: 100%) */
  width?: string | number;
  /** Border radius (default: 4px) */
  radius?: string | number;
  /** Custom className for additional styling */
  className?: string;
}

export function Skeleton({
  height = 16,
  width = "100%",
  radius = 4,
  className = "",
}: SkeletonProps) {
  const style = {
    height: typeof height === "number" ? `${height}px` : height,
    width: typeof width === "number" ? `${width}px` : width,
    borderRadius: typeof radius === "number" ? `${radius}px` : radius,
  };

  return (
    <div
      className={`animate-loading bg-gradient-to-r from-gray-100 via-gray-200 to-gray-100 bg-[length:200%_100%] ${className}`}
      style={style}
    />
  );
}

/** Circular loading spinner with optional title and description */
export interface SpinnerProps {
  /** Size of spinner in pixels (default: 40) */
  size?: number;
  /** Optional title text below spinner */
  title?: string;
  /** Optional description text below title */
  description?: string;
  /** Whether to center the spinner (default: true) */
  center?: boolean;
}

export function Spinner({
  size = 40,
  title,
  description,
  center = true,
}: SpinnerProps) {
  const spinnerStyle = {
    width: `${size}px`,
    height: `${size}px`,
    border: `${size / 10}px solid #f0f0f0`,
    borderTopColor: "#333",
  };

  const content = (
    <>
      <div
        className="animate-spin rounded-full"
        style={spinnerStyle}
        role="status"
        aria-label="Loading"
      />
      {title && (
        <div className="mt-16 text-18 font-semibold text-gray-700">{title}</div>
      )}
      {description && (
        <div className="mt-8 max-w-[400px] text-14 text-gray-600">
          {description}
        </div>
      )}
    </>
  );

  if (center) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-20 py-40 text-center">
        {content}
      </div>
    );
  }

  return <div className="flex flex-col items-center">{content}</div>;
}

/** Message skeleton for loading chat messages */
export function MessageSkeleton() {
  return (
    <div className="mb-16 flex gap-12">
      {/* Avatar */}
      <Skeleton height={32} width={32} radius="50%" />

      {/* Message content */}
      <div className="flex-1">
        <Skeleton height={16} width="100%" className="mb-8" />
        <Skeleton height={16} width="80%" className="mb-8" />
        <Skeleton height={16} width="60%" />
      </div>
    </div>
  );
}

/** Sidebar session item skeleton */
export function SessionItemSkeleton() {
  return <Skeleton height={40} width="100%" radius={4} className="mb-8" />;
}

/** Card skeleton for loading tool cards, settings cards, etc. */
export function CardSkeleton({ height = 120 }: { height?: number }) {
  return <Skeleton height={height} width="100%" radius={8} className="mb-12" />;
}

/** Loading state with streaming response indicator (blinking cursor) */
export interface StreamingIndicatorProps {
  /** Text being streamed */
  text?: string;
  /** Whether to show blinking cursor */
  showCursor?: boolean;
}

export function StreamingIndicator({
  text = "",
  showCursor = true,
}: StreamingIndicatorProps) {
  return (
    <div className="inline">
      {text}
      {showCursor && (
        <span className="ml-4 inline-block h-16 w-8 animate-blink bg-gray-700 align-baseline" />
      )}
    </div>
  );
}

/**
 * ErrorBanner component
 *
 * Displays error messages with retry/dismiss actions.
 * Categorizes errors for better user feedback.
 */

"use client";

export interface ErrorBannerProps {
  /** Error message or Error object */
  error: string | Error;
  /** Optional retry callback */
  onRetry?: () => void;
  /** Optional dismiss callback */
  onDismiss?: () => void;
}

/**
 * Categorize error for better user messaging
 */
function categorizeError(error: string | Error): {
  message: string;
  category: "network" | "api" | "validation" | "unknown";
} {
  const errorText = error instanceof Error ? error.message : error;
  const lowerError = errorText.toLowerCase();

  // Network errors
  if (
    lowerError.includes("network") ||
    lowerError.includes("fetch") ||
    lowerError.includes("connection") ||
    lowerError.includes("offline")
  ) {
    return {
      message: "Network error - please check your connection and try again",
      category: "network",
    };
  }

  // API errors
  if (
    lowerError.includes("http") ||
    lowerError.includes("401") ||
    lowerError.includes("403") ||
    lowerError.includes("404") ||
    lowerError.includes("500")
  ) {
    return {
      message: `API error - ${errorText}`,
      category: "api",
    };
  }

  // Validation errors
  if (lowerError.includes("invalid") || lowerError.includes("required")) {
    return {
      message: errorText,
      category: "validation",
    };
  }

  // Unknown errors
  return {
    message: errorText || "An unexpected error occurred",
    category: "unknown",
  };
}

export function ErrorBanner({ error, onRetry, onDismiss }: ErrorBannerProps) {
  const { message, category } = categorizeError(error);

  // Don't show validation errors in banner (should be inline)
  if (category === "validation") {
    return null;
  }

  return (
    <div
      className="border-t border-red-DEFAULT bg-red-bg px-20 py-12"
      role="alert"
      aria-live="assertive"
      data-testid="error-banner"
    >
      <div className="flex items-center justify-between gap-12">
        {/* Error icon and message */}
        <div className="flex items-center gap-8 text-14 text-red-dark">
          <span className="text-16">⚠️</span>
          <span>{message}</span>
        </div>

        {/* Actions */}
        <div className="flex gap-8">
          {onRetry && category === "network" && (
            <button
              onClick={onRetry}
              className="rounded-6 bg-red-DEFAULT px-16 py-8 text-13 font-medium text-white hover:opacity-90 transition-opacity"
              aria-label="Retry action"
            >
              Retry
            </button>
          )}
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="rounded-6 border border-red-DEFAULT px-16 py-8 text-13 font-medium text-red-dark hover:bg-red-light transition-colors"
              aria-label="Dismiss error"
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

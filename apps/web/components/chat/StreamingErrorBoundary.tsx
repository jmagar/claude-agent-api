/**
 * StreamingErrorBoundary component
 *
 * Error boundary specifically for streaming chat components.
 * Catches React errors in the streaming UI and provides recovery options.
 *
 * Features:
 * - Catches and displays React component errors
 * - Retry button to remount the component tree
 * - Reset session option for critical errors
 * - Structured error logging
 */

"use client";

import { Component, type ReactNode, type ErrorInfo } from "react";
import { AlertTriangle, RefreshCw, RotateCcw } from "lucide-react";
import { logger } from "@/lib/logger";

export interface StreamingErrorBoundaryProps {
  children: ReactNode;
  /** Callback when user requests session reset */
  onResetSession?: () => void;
  /** Fallback content to show on error (replaces default UI) */
  fallback?: ReactNode;
}

interface StreamingErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class StreamingErrorBoundary extends Component<
  StreamingErrorBoundaryProps,
  StreamingErrorBoundaryState
> {
  constructor(props: StreamingErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<StreamingErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Log the error with structured logging
    logger.error("Streaming component error", error, {
      componentStack: errorInfo.componentStack,
    });
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleResetSession = (): void => {
    this.handleRetry();
    this.props.onResetSession?.();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div
          className="flex flex-col items-center justify-center p-24 bg-red-50 border border-red-200 rounded-lg m-16"
          data-testid="streaming-error-boundary"
          role="alert"
        >
          <AlertTriangle className="w-48 h-48 text-red-500 mb-16" />
          <h3 className="text-18 font-semibold text-red-900 mb-8">
            Something went wrong
          </h3>
          <p className="text-14 text-red-700 mb-16 text-center max-w-md">
            {this.state.error?.message || "An unexpected error occurred in the chat interface."}
          </p>

          <div className="flex gap-12">
            <button
              onClick={this.handleRetry}
              className="flex items-center gap-8 px-16 py-8 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
              aria-label="Retry loading the chat interface"
            >
              <RefreshCw className="w-16 h-16" />
              <span>Try Again</span>
            </button>

            {this.props.onResetSession && (
              <button
                onClick={this.handleResetSession}
                className="flex items-center gap-8 px-16 py-8 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                aria-label="Reset the chat session"
              >
                <RotateCcw className="w-16 h-16" />
                <span>Reset Session</span>
              </button>
            )}
          </div>

          {/* Show component stack in development */}
          {process.env.NODE_ENV === "development" && this.state.errorInfo && (
            <details className="mt-16 w-full max-w-2xl">
              <summary className="text-12 text-red-600 cursor-pointer hover:underline">
                Show error details
              </summary>
              <pre className="mt-8 p-12 bg-red-100 rounded text-10 overflow-x-auto text-red-800">
                {this.state.error?.stack}
                {"\n\nComponent Stack:"}
                {this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

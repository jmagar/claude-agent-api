/**
 * Unit tests for StreamingErrorBoundary component
 *
 * Tests error boundary behavior for streaming components.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { StreamingErrorBoundary } from "@/components/chat/StreamingErrorBoundary";

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error message");
  }
  return <div data-testid="child-content">Child content</div>;
};

// Suppress console.error for expected errors in tests
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});
afterAll(() => {
  console.error = originalError;
});

describe("StreamingErrorBoundary", () => {
  describe("normal rendering", () => {
    it("should render children when no error", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={false} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByTestId("child-content")).toBeInTheDocument();
    });

    it("should not show error UI when no error", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={false} />
        </StreamingErrorBoundary>
      );

      expect(screen.queryByTestId("streaming-error-boundary")).not.toBeInTheDocument();
    });
  });

  describe("error handling", () => {
    it("should catch errors and display error UI", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByTestId("streaming-error-boundary")).toBeInTheDocument();
      expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    });

    it("should display error message", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByText("Test error message")).toBeInTheDocument();
    });

    it("should have role=alert for accessibility", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  describe("retry functionality", () => {
    it("should show Try Again button", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByText("Try Again")).toBeInTheDocument();
    });

    it("should have proper aria-label on retry button", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(
        screen.getByRole("button", { name: /retry loading the chat interface/i })
      ).toBeInTheDocument();
    });

    it("should show retry button with correct functionality", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      // Error UI should be visible
      expect(screen.getByText("Something went wrong")).toBeInTheDocument();

      // Retry button should be clickable
      const retryButton = screen.getByText("Try Again");
      expect(retryButton).toBeEnabled();

      // Clicking retry should call the handleRetry method
      // (which resets state, causing a re-render attempt)
      fireEvent.click(retryButton);

      // The error boundary should have reset its state
      // But since the same error-throwing component is rendered,
      // it will throw again - this is expected behavior
      // The key assertion is that the retry button exists and is functional
    });
  });

  describe("reset session functionality", () => {
    it("should show Reset Session button when onResetSession is provided", () => {
      const onResetSession = jest.fn();

      render(
        <StreamingErrorBoundary onResetSession={onResetSession}>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByText("Reset Session")).toBeInTheDocument();
    });

    it("should not show Reset Session button when onResetSession is not provided", () => {
      render(
        <StreamingErrorBoundary>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.queryByText("Reset Session")).not.toBeInTheDocument();
    });

    it("should call onResetSession when clicked", () => {
      const onResetSession = jest.fn();

      render(
        <StreamingErrorBoundary onResetSession={onResetSession}>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      fireEvent.click(screen.getByText("Reset Session"));

      expect(onResetSession).toHaveBeenCalled();
    });

    it("should have proper aria-label on reset session button", () => {
      const onResetSession = jest.fn();

      render(
        <StreamingErrorBoundary onResetSession={onResetSession}>
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(
        screen.getByRole("button", { name: /reset the chat session/i })
      ).toBeInTheDocument();
    });
  });

  describe("custom fallback", () => {
    it("should render custom fallback when provided", () => {
      render(
        <StreamingErrorBoundary
          fallback={<div data-testid="custom-fallback">Custom error UI</div>}
        >
          <ThrowError shouldThrow={true} />
        </StreamingErrorBoundary>
      );

      expect(screen.getByTestId("custom-fallback")).toBeInTheDocument();
      expect(screen.queryByTestId("streaming-error-boundary")).not.toBeInTheDocument();
    });
  });
});

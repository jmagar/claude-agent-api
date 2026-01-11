/**
 * Integration tests for chat flow
 * RED phase - Test-Driven Development
 *
 * Testing requirements from spec.md User Story 1:
 * - End-to-end chat interaction flow
 * - Message sending and receiving
 * - SSE streaming integration
 * - Message persistence in session
 * - Error handling during streaming
 */

import { render, screen, fireEvent, waitFor } from "@/tests/utils/test-utils";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { fetchEventSource } from "@microsoft/fetch-event-source";

jest.mock("@microsoft/fetch-event-source", () => ({
  fetchEventSource: jest.fn(),
}));

const fetchEventSourceMock = fetchEventSource as jest.Mock;

const createOkResponse = () => ({
  ok: true,
  status: 200,
  statusText: "OK",
});

const mockStream = (events: Array<{ event: string; data: unknown }>) => {
  fetchEventSourceMock.mockImplementation(async (_url, options) => {
    await options.onopen?.(createOkResponse());
    events.forEach((evt) => {
      options.onmessage?.({
        event: evt.event,
        data: JSON.stringify(evt.data),
      });
    });
  });
};

const mockErrorStream = (status: number, statusText: string) => {
  fetchEventSourceMock.mockImplementation(async (_url, options) => {
    await options.onopen?.({ ok: false, status, statusText });
    throw new Error(`HTTP ${status}: ${statusText}`);
  });
};

const mockNetworkError = () => {
  fetchEventSourceMock.mockImplementation(async (_url, options) => {
    options.onerror?.(new Error("Network error"));
    throw new Error("Network error");
  });
};

beforeEach(() => {
  fetchEventSourceMock.mockReset();
  global.fetch = jest.fn().mockResolvedValue(
    new Response(JSON.stringify({ messages: [], total: 0 }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  );
});

describe("Chat Flow Integration", () => {
  describe("Basic message sending", () => {
    it("should send user message and receive streaming response", async () => {
      mockStream([
        { event: "init", data: { session_id: "session-123" } },
        {
          event: "message",
          data: { content: [{ type: "text", text: "Hello! " }], role: "assistant" },
        },
        {
          event: "message",
          data: { content: [{ type: "text", text: "How can I help" }], role: "assistant" },
        },
        {
          event: "message",
          data: { content: [{ type: "text", text: " you today?" }], role: "assistant" },
        },
        { event: "done", data: { usage: { input_tokens: 10, output_tokens: 5 } } },
      ]);

      render(<ChatInterface sessionId="session-123" />);

      // Type a message
      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Hello, Claude!" } });

      // Send message
      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // User message should appear immediately
      await waitFor(() => {
        expect(screen.getByText("Hello, Claude!")).toBeInTheDocument();
      });

      // Wait for streaming response
      await waitFor(() => {
        expect(screen.getByText(/Hello! How can I help you today?/)).toBeInTheDocument();
      });

      // Composer should be cleared
      expect(textarea).toHaveValue("");
    });

    it("should display streaming tokens incrementally", async () => {
      mockStream([
        { event: "init", data: { session_id: "session-123" } },
        {
          event: "message",
          data: { content: [{ type: "text", text: "Hello! " }], role: "assistant" },
        },
        {
          event: "message",
          data: { content: [{ type: "text", text: "How can I help" }], role: "assistant" },
        },
        {
          event: "message",
          data: { content: [{ type: "text", text: " you today?" }], role: "assistant" },
        },
        { event: "done", data: { usage: { input_tokens: 10, output_tokens: 5 } } },
      ]);

      render(<ChatInterface sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Should show streaming indicator during response
      await waitFor(() => {
        expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
      });

      // Final message should appear
      await waitFor(() => {
        expect(screen.getByText(/Hello! How can I help you today?/)).toBeInTheDocument();
      });

      // Streaming indicator should disappear
      expect(
        screen.queryByTestId("streaming-indicator")
      ).not.toBeInTheDocument();
    });

    it("should disable composer during streaming", async () => {
      mockStream([
        { event: "init", data: { session_id: "session-123" } },
        {
          event: "message",
          data: { content: [{ type: "text", text: "Hello! " }], role: "assistant" },
        },
        { event: "done", data: { usage: { input_tokens: 10, output_tokens: 5 } } },
      ]);

      render(<ChatInterface sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Composer should be disabled during streaming
      await waitFor(() => {
        expect(textarea).toBeDisabled();
        expect(sendButton).toBeDisabled();
      });

      // Should re-enable after streaming completes
      await waitFor(() => {
        expect(textarea).not.toBeDisabled();
      });

      fireEvent.change(textarea, { target: { value: "Next message" } });
      expect(sendButton).not.toBeDisabled();
    });

    it("should auto-scroll to new messages", async () => {
      mockStream([
        { event: "init", data: { session_id: "session-123" } },
        {
          event: "message",
          data: { content: [{ type: "text", text: "Hello! " }], role: "assistant" },
        },
        { event: "done", data: { usage: { input_tokens: 10, output_tokens: 5 } } },
      ]);

      render(<ChatInterface sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // New assistant message should appear in the list
      await waitFor(() => {
        expect(screen.getByText(/Hello!/)).toBeInTheDocument();
      });
    });
  });

  describe("Error handling", () => {
    it("should display error message when streaming fails", async () => {
      mockErrorStream(500, "Internal Server Error");

      render(<ChatInterface sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Should show API error message
      await waitFor(() => {
        expect(
          screen.getByText(/api error/i)
        ).toBeInTheDocument();
      });
    });

    it("should allow retry after error", async () => {
      let requestCount = 0;
      fetchEventSourceMock.mockImplementation(async (_url, options) => {
        requestCount++;
        if (requestCount === 1) {
          await options.onopen?.({ ok: false, status: 500, statusText: "Internal Server Error" });
          throw new Error("HTTP 500: Internal Server Error");
        }

        await options.onopen?.(createOkResponse());
        options.onmessage?.({
          event: "message",
          data: JSON.stringify({
            content: [{ type: "text", text: "Success" }],
            role: "assistant",
          }),
        });
        options.onmessage?.({ event: "done", data: JSON.stringify({}) });
      });

      render(<ChatInterface sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/api error/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole("button", { name: /retry/i });
      fireEvent.click(retryButton);

      // Should show success message
      await waitFor(() => {
        expect(screen.getByText("Success")).toBeInTheDocument();
      });
    });

    it("should handle network errors gracefully", async () => {
      mockNetworkError();

      render(<ChatInterface sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Should show network error
      await waitFor(() => {
        expect(
          screen.getByText(/network error/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Message persistence", () => {
    it("should load existing messages on mount", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            messages: [
              {
                id: "msg-1",
                role: "user",
                content: [{ type: "text", text: "Previous message" }],
                created_at: new Date().toISOString(),
              },
              {
                id: "msg-2",
                role: "assistant",
                content: [{ type: "text", text: "Previous response" }],
                created_at: new Date().toISOString(),
              },
            ],
            total: 2,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      render(<ChatInterface sessionId="session-123" />);

      // Should load and display existing messages
      await waitFor(() => {
        expect(screen.getByText("Previous message")).toBeInTheDocument();
        expect(screen.getByText("Previous response")).toBeInTheDocument();
      });
    });

    it("should append new messages to existing conversation", async () => {
      mockStream([
        { event: "init", data: { session_id: "session-123" } },
        {
          event: "message",
          data: { content: [{ type: "text", text: "Second message" }], role: "assistant" },
        },
        { event: "done", data: {} },
      ]);

      (global.fetch as jest.Mock).mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            messages: [
              {
                id: "msg-1",
                role: "user",
                content: [{ type: "text", text: "First message" }],
                created_at: new Date().toISOString(),
              },
            ],
            total: 1,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      );

      render(<ChatInterface sessionId="session-123" />);

      // Wait for existing message
      await waitFor(() => {
        expect(screen.getByText("First message")).toBeInTheDocument();
      });

      // Send new message
      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Second message" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Both messages should be visible
      await waitFor(() => {
        expect(screen.getByText("First message")).toBeInTheDocument();
        expect(screen.getByText("Second message")).toBeInTheDocument();
      });
    });
  });

  describe("Loading states", () => {
    it("should show loading skeleton while fetching initial messages", () => {
      render(<ChatInterface sessionId="session-123" />);

      // Should show loading state
      expect(screen.getByTestId("message-skeleton")).toBeInTheDocument();
    });

    it("should hide loading skeleton after messages load", async () => {
      render(<ChatInterface sessionId="session-123" />);

      // Wait for messages to load
      await waitFor(() => {
        expect(
          screen.queryByTestId("message-skeleton")
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("Empty state", () => {
    it("should show empty state when no messages", async () => {
      render(<ChatInterface sessionId="session-123" />);

      await waitFor(() => {
        expect(screen.getByText(/no messages yet/i)).toBeInTheDocument();
      });
    });

    it("should hide empty state after first message", async () => {
      render(<ChatInterface sessionId="session-123" />);

      // Send first message
      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "First message" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      // Empty state should disappear
      await waitFor(() => {
        expect(
          screen.queryByText(/no messages yet/i)
        ).not.toBeInTheDocument();
      });
    });
  });
});

/**
 * Unit tests for MessageItem component
 * RED phase - Test-Driven Development
 *
 * Testing requirements from spec.md User Story 1:
 * - Display message bubbles with correct styling for role
 * - Render text content with markdown support
 * - Display thinking blocks (collapsible)
 * - Display tool use/result blocks
 * - Show timestamps
 * - Handle long messages with proper overflow
 */

import { render, screen, fireEvent } from "@/tests/utils/test-utils";
import { MessageItem } from "@/components/chat/MessageItem";
import type { Message } from "@/types";

describe("MessageItem", () => {
  describe("User messages", () => {
    const userMessage: Message = {
      id: "msg-1",
      role: "user",
      content: [
        {
          type: "text",
          text: "Hello, Claude!",
        },
      ],
      created_at: new Date("2026-01-10T10:00:00Z"),
    };

    it("should render user message with correct styling", () => {
      render(<MessageItem message={userMessage} />);

      // Should have user role attribute
      const messageEl = screen.getByTestId("message-item");
      expect(messageEl).toHaveAttribute("data-role", "user");

      // Should display message text
      expect(screen.getByText("Hello, Claude!")).toBeInTheDocument();
    });

    it("should display 'You' label for user messages", () => {
      render(<MessageItem message={userMessage} />);

      expect(screen.getByText(/you/i)).toBeInTheDocument();
    });

    it("should align user messages to the right", () => {
      render(<MessageItem message={userMessage} />);

      const messageEl = screen.getByTestId("message-item");
      expect(messageEl).toHaveClass("justify-end");
    });

    it("should use blue background for user message bubbles", () => {
      render(<MessageItem message={userMessage} />);

      const bubble = screen.getByTestId("message-bubble");
      expect(bubble).toHaveClass("bg-blue-light");
      expect(bubble).toHaveClass("border-blue-border");
    });
  });

  describe("Assistant messages", () => {
    const assistantMessage: Message = {
      id: "msg-2",
      role: "assistant",
      content: [
        {
          type: "text",
          text: "Hello! How can I help you today?",
        },
      ],
      created_at: new Date("2026-01-10T10:00:01Z"),
    };

    it("should render assistant message with correct styling", () => {
      render(<MessageItem message={assistantMessage} />);

      const messageEl = screen.getByTestId("message-item");
      expect(messageEl).toHaveAttribute("data-role", "assistant");

      expect(
        screen.getByText("Hello! How can I help you today?")
      ).toBeInTheDocument();
    });

    it("should display 'Assistant' label for assistant messages", () => {
      render(<MessageItem message={assistantMessage} />);

      expect(screen.getByText(/assistant/i)).toBeInTheDocument();
    });

    it("should align assistant messages to the left", () => {
      render(<MessageItem message={assistantMessage} />);

      const messageEl = screen.getByTestId("message-item");
      expect(messageEl).not.toHaveClass("justify-end");
    });

    it("should use gray background for assistant message bubbles", () => {
      render(<MessageItem message={assistantMessage} />);

      const bubble = screen.getByTestId("message-bubble");
      expect(bubble).toHaveClass("bg-gray-100");
    });
  });

  describe("Content rendering", () => {
    it("should render markdown in text content", () => {
      const messageWithMarkdown: Message = {
        id: "msg-3",
        role: "assistant",
        content: [
          {
            type: "text",
            text: "Here's some **bold** and *italic* text with `code`.",
          },
        ],
        created_at: new Date("2026-01-10T10:00:02Z"),
      };

      render(<MessageItem message={messageWithMarkdown} />);

      // Markdown should be rendered
      const strong = screen.getByText("bold");
      expect(strong.tagName).toBe("STRONG");

      const em = screen.getByText("italic");
      expect(em.tagName).toBe("EM");

      const code = screen.getByText("code");
      expect(code.tagName).toBe("CODE");
    });

    it("should render thinking blocks as collapsible", () => {
      const messageWithThinking: Message = {
        id: "msg-4",
        role: "assistant",
        content: [
          {
            type: "thinking",
            thinking: "Let me analyze this carefully...",
          },
          {
            type: "text",
            text: "Based on my analysis, here's the answer.",
          },
        ],
        created_at: new Date("2026-01-10T10:00:03Z"),
      };

      render(<MessageItem message={messageWithThinking} />);

      // Thinking block should be collapsible
      const thinkingToggle = screen.getByText(/thinking/i);
      expect(thinkingToggle).toBeInTheDocument();

      // Content should be hidden by default
      expect(
        screen.queryByText("Let me analyze this carefully...")
      ).not.toBeVisible();

      // Click to expand
      fireEvent.click(thinkingToggle);
      expect(
        screen.getByText("Let me analyze this carefully...")
      ).toBeVisible();
    });

    it("should render tool use blocks", () => {
      const messageWithToolUse: Message = {
        id: "msg-5",
        role: "assistant",
        content: [
          {
            type: "tool_use",
            id: "tool-1",
            name: "Read",
            input: {
              file_path: "/src/app.tsx",
            },
          },
        ],
        created_at: new Date("2026-01-10T10:00:04Z"),
      };

      render(<MessageItem message={messageWithToolUse} />);

      // Tool card should be displayed
      expect(screen.getByText("Read")).toBeInTheDocument();
      expect(screen.getByText(/file_path/i)).toBeInTheDocument();
    });

    it("should render tool result blocks", () => {
      const messageWithToolResult: Message = {
        id: "msg-6",
        role: "user",
        content: [
          {
            type: "tool_result",
            tool_use_id: "tool-1",
            content: "File contents here...",
          },
        ],
        created_at: new Date("2026-01-10T10:00:05Z"),
      };

      render(<MessageItem message={messageWithToolResult} />);

      // Tool result should be displayed
      expect(screen.getByText("File contents here...")).toBeInTheDocument();
    });

    it("should handle multiple content blocks", () => {
      const messageWithMultipleBlocks: Message = {
        id: "msg-7",
        role: "assistant",
        content: [
          {
            type: "text",
            text: "Let me check that file.",
          },
          {
            type: "tool_use",
            id: "tool-2",
            name: "Read",
            input: { file_path: "/test.ts" },
          },
          {
            type: "text",
            text: "Here's what I found.",
          },
        ],
        created_at: new Date("2026-01-10T10:00:06Z"),
      };

      render(<MessageItem message={messageWithMultipleBlocks} />);

      // All blocks should be rendered
      expect(screen.getByText("Let me check that file.")).toBeInTheDocument();
      expect(screen.getByText("Read")).toBeInTheDocument();
      expect(screen.getByText("Here's what I found.")).toBeInTheDocument();
    });
  });

  describe("Timestamps", () => {
    it("should display formatted timestamp", () => {
      const message: Message = {
        id: "msg-8",
        role: "user",
        content: [{ type: "text", text: "Test" }],
        created_at: new Date("2026-01-10T10:30:45Z"),
      };

      render(<MessageItem message={message} showTimestamp={true} />);

      // Should show time (format: HH:MM)
      expect(screen.getByText(/10:30/)).toBeInTheDocument();
    });

    it("should hide timestamp when showTimestamp is false", () => {
      const message: Message = {
        id: "msg-9",
        role: "user",
        content: [{ type: "text", text: "Test" }],
        created_at: new Date("2026-01-10T10:30:45Z"),
      };

      render(<MessageItem message={message} showTimestamp={false} />);

      // Timestamp should not be visible
      expect(screen.queryByText(/10:30/)).not.toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA attributes", () => {
      const message: Message = {
        id: "msg-10",
        role: "assistant",
        content: [{ type: "text", text: "Test message" }],
        created_at: new Date("2026-01-10T10:00:00Z"),
      };

      render(<MessageItem message={message} />);

      const messageEl = screen.getByTestId("message-item");
      expect(messageEl).toHaveAttribute("role", "article");
      expect(messageEl).toHaveAttribute("aria-label");
    });
  });
});

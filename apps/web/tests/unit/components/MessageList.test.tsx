/**
 * Unit tests for MessageList component
 * RED phase - Test-Driven Development
 *
 * Testing requirements from spec.md User Story 1:
 * - Display messages in chronological order
 * - Support virtualized scrolling for performance
 * - Auto-scroll to bottom on new messages
 * - Handle empty message lists
 * - Render user and assistant message bubbles correctly
 */

import { render, screen, waitFor } from "@/tests/utils/test-utils";
import { MessageList } from "@/components/chat/MessageList";
import type { Message } from "@/types";

describe("MessageList", () => {
  const mockMessages: Message[] = [
    {
      id: "msg-1",
      role: "user",
      content: [
        {
          type: "text",
          text: "Hello, Claude!",
        },
      ],
      created_at: new Date("2026-01-10T10:00:00Z"),
    },
    {
      id: "msg-2",
      role: "assistant",
      content: [
        {
          type: "text",
          text: "Hello! How can I help you today?",
        },
      ],
      created_at: new Date("2026-01-10T10:00:01Z"),
    },
    {
      id: "msg-3",
      role: "user",
      content: [
        {
          type: "text",
          text: "Can you help me understand TypeScript?",
        },
      ],
      created_at: new Date("2026-01-10T10:00:05Z"),
    },
  ];

  describe("Rendering", () => {
    it("should render empty state when no messages", () => {
      render(<MessageList messages={[]} />);

      // Should show empty state
      expect(
        screen.getByText(/no messages yet/i)
      ).toBeInTheDocument();
    });

    it("should render all messages in chronological order", () => {
      render(<MessageList messages={mockMessages} />);

      // All messages should be visible
      expect(screen.getByText("Hello, Claude!")).toBeInTheDocument();
      expect(
        screen.getByText("Hello! How can I help you today?")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Can you help me understand TypeScript?")
      ).toBeInTheDocument();
    });

    it("should distinguish user and assistant messages visually", () => {
      render(<MessageList messages={mockMessages} />);

      // User messages should have user styling
      const userMessage = screen.getByText("Hello, Claude!");
      expect(userMessage.closest("[data-role='user']")).toBeInTheDocument();

      // Assistant messages should have assistant styling
      const assistantMessage = screen.getByText(
        "Hello! How can I help you today?"
      );
      expect(
        assistantMessage.closest("[data-role='assistant']")
      ).toBeInTheDocument();
    });

    it("should display message labels (User/Assistant)", () => {
      render(<MessageList messages={mockMessages} />);

      // Should show role labels
      const userLabels = screen.getAllByText(/you/i);
      const assistantLabels = screen.getAllByText(/assistant/i);

      expect(userLabels.length).toBeGreaterThan(0);
      expect(assistantLabels.length).toBeGreaterThan(0);
    });
  });

  describe("Scrolling behavior", () => {
    it("should render newly added messages", async () => {
      const { rerender } = render(<MessageList messages={mockMessages} />);

      // Add new message
      const newMessage: Message = {
        id: "msg-4",
        role: "assistant",
        content: [
          {
            type: "text",
            text: "TypeScript is a statically typed superset of JavaScript.",
          },
        ],
        created_at: new Date("2026-01-10T10:00:10Z"),
      };

      rerender(<MessageList messages={[...mockMessages, newMessage]} />);

      // New message should appear in the list
      await waitFor(() => {
        expect(
          screen.getByText(
            "TypeScript is a statically typed superset of JavaScript."
          )
        ).toBeInTheDocument();
      });
    });

    it("should have scrollable container for overflow", () => {
      render(<MessageList messages={mockMessages} />);

      // Container should have overflow-auto class for scrolling
      const container = screen.getByTestId("message-list-container");
      expect(container).toHaveClass("overflow-auto");
    });
  });

  describe("Performance", () => {
    it("should use virtualization for large message lists", () => {
      // Create 100 messages
      const manyMessages: Message[] = Array.from({ length: 100 }, (_, i) => ({
        id: `msg-${i}`,
        role: i % 2 === 0 ? "user" : "assistant",
        content: [
          {
            type: "text",
            text: `Message ${i}`,
          },
        ],
        created_at: new Date(`2026-01-10T10:00:${String(i).padStart(2, "0")}Z`),
      }));

      render(<MessageList messages={manyMessages} />);

      // Should render virtualization scroller
      const container = screen.getByTestId("message-list-container");
      expect(container).toBeInTheDocument();
      expect(container).toHaveAttribute("data-virtuoso-scroller");
    });
  });

  describe("Loading state", () => {
    it("should show loading skeleton when isLoading is true", () => {
      render(<MessageList messages={[]} isLoading={true} />);

      // Should show skeleton loaders
      expect(screen.getByTestId("message-skeleton")).toBeInTheDocument();
    });

    it("should show streaming indicator on last message when isStreaming is true", () => {
      render(<MessageList messages={mockMessages} isStreaming={true} />);

      // Should show blinking cursor or streaming indicator
      expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels", () => {
      render(<MessageList messages={mockMessages} />);

      // Container should have role and label
      const container = screen.getByRole("log");
      expect(container).toHaveAttribute("aria-label", "Chat messages");
    });

    it("should have proper message structure for screen readers", () => {
      render(<MessageList messages={mockMessages} />);

      // Each message should have proper role
      const userMessage = screen.getByText("Hello, Claude!");
      expect(userMessage.closest("[role='article']")).toBeInTheDocument();
    });
  });
});

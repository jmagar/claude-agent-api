/**
 * Unit tests for Composer component
 * RED phase - Test-Driven Development
 *
 * Testing requirements from spec.md User Story 1:
 * - Textarea input with auto-resize
 * - Shift+Enter for multiline (Enter to send)
 * - Send button (disabled when empty)
 * - Draft message persistence in localStorage
 * - Clear input after send
 * - Handle loading state (disable during response)
 */

import { render, screen, fireEvent, waitFor, act } from "@/tests/utils/test-utils";
import { Composer } from "@/components/chat/Composer";
import { mockLocalStorage } from "@/tests/utils/test-utils";

describe("Composer", () => {
  let mockOnSend: jest.Mock;

  beforeEach(() => {
    mockOnSend = jest.fn();
    Object.defineProperty(window, "localStorage", {
      value: mockLocalStorage(),
      writable: true,
    });
  });

  describe("Rendering", () => {
    it("should render textarea and send button", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      expect(textarea).toBeInTheDocument();
      expect(textarea.tagName).toBe("TEXTAREA");

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).toBeInTheDocument();
    });

    it("should have proper placeholder text", () => {
      render(<Composer onSend={mockOnSend} />);

      expect(
        screen.getByPlaceholderText(/message claude/i)
      ).toBeInTheDocument();
    });

    it("should disable send button when textarea is empty", () => {
      render(<Composer onSend={mockOnSend} />);

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it("should enable send button when textarea has text", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Hello" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).not.toBeDisabled();
    });
  });

  describe("Input handling", () => {
    it("should update textarea value on input", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(
        /message/i
      ) as HTMLTextAreaElement;
      fireEvent.change(textarea, { target: { value: "Test message" } });

      expect(textarea.value).toBe("Test message");
    });

    it("should trim whitespace-only input and treat as empty", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "   " } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it("should allow multiline input with Shift+Enter", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(
        /message/i
      ) as HTMLTextAreaElement;

      // Type first line
      fireEvent.change(textarea, { target: { value: "Line 1" } });

      // Press Shift+Enter (should NOT send)
      fireEvent.keyDown(textarea, {
        key: "Enter",
        shiftKey: true,
        code: "Enter",
      });

      expect(mockOnSend).not.toHaveBeenCalled();

      // Add second line
      fireEvent.change(textarea, { target: { value: "Line 1\nLine 2" } });
      expect(textarea.value).toBe("Line 1\nLine 2");
    });

    it("should auto-resize textarea as content grows", async () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(
        /message/i
      ) as HTMLTextAreaElement;

      // Add multiline content
      const longText = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5";
      fireEvent.change(textarea, { target: { value: longText } });

      // Height should be set (auto-resize effect ran)
      await waitFor(() => {
        expect(textarea.style.height).toBeTruthy();
        expect(textarea.style.height).toMatch(/\d+px/);
      });
    });

    it("should enforce max height and scroll when exceeded", () => {
      render(<Composer onSend={mockOnSend} maxHeight={80} />);

      const textarea = screen.getByPlaceholderText(/message/i);

      // Should have max-height constraint
      expect(textarea).toHaveStyle({ maxHeight: "80px" });
    });
  });

  describe("Sending messages", () => {
    it("should call onSend when Enter key is pressed", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test message" } });

      fireEvent.keyDown(textarea, {
        key: "Enter",
        code: "Enter",
        shiftKey: false,
      });

      expect(mockOnSend).toHaveBeenCalledWith("Test message");
    });

    it("should call onSend when send button is clicked", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test message" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      expect(mockOnSend).toHaveBeenCalledWith("Test message");
    });

    it("should clear textarea after sending", async () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(
        /message/i
      ) as HTMLTextAreaElement;
      fireEvent.change(textarea, { target: { value: "Test message" } });

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(textarea.value).toBe("");
      });
    });

    it("should not send empty messages", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.keyDown(textarea, { key: "Enter", code: "Enter" });

      expect(mockOnSend).not.toHaveBeenCalled();
    });

    it("should prevent default Enter behavior to avoid form submission", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      const event = new KeyboardEvent("keydown", {
        key: "Enter",
        code: "Enter",
        bubbles: true,
      });
      const preventDefaultSpy = jest.spyOn(event, "preventDefault");

      act(() => {
        textarea.dispatchEvent(event);
      });

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe("Loading state", () => {
    it("should disable textarea when isLoading is true", () => {
      render(<Composer onSend={mockOnSend} isLoading={true} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      expect(textarea).toBeDisabled();
    });

    it("should disable send button when isLoading is true", () => {
      render(<Composer onSend={mockOnSend} isLoading={true} />);

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).toBeDisabled();
    });

    it("should show loading indicator when isLoading is true", () => {
      render(<Composer onSend={mockOnSend} isLoading={true} />);

      expect(screen.getByTestId("composer-loading")).toBeInTheDocument();
    });

    it("should not send messages when isLoading is true", () => {
      render(<Composer onSend={mockOnSend} isLoading={true} />);

      const textarea = screen.getByPlaceholderText(/message/i);

      // Try to send (should be prevented)
      fireEvent.keyDown(textarea, { key: "Enter", code: "Enter" });

      expect(mockOnSend).not.toHaveBeenCalled();
    });
  });

  describe("Draft persistence", () => {
    it("should save draft to localStorage on input", async () => {
      render(<Composer onSend={mockOnSend} sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Draft message" } });

      await waitFor(() => {
        const draft = localStorage.getItem("draft:session-123");
        expect(draft).toBe("Draft message");
      });
    });

    it("should load draft from localStorage on mount", () => {
      localStorage.setItem("draft:session-123", "Saved draft");

      render(<Composer onSend={mockOnSend} sessionId="session-123" />);

      const textarea = screen.getByPlaceholderText(
        /message/i
      ) as HTMLTextAreaElement;
      expect(textarea.value).toBe("Saved draft");
    });

    it("should clear draft from localStorage after sending", async () => {
      localStorage.setItem("draft:session-123", "Draft message");

      render(<Composer onSend={mockOnSend} sessionId="session-123" />);

      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      await waitFor(() => {
        const draft = localStorage.getItem("draft:session-123");
        expect(draft).toBeNull();
      });
    });

    it("should clear draft when switching to a session without a saved draft", async () => {
      localStorage.setItem("draft:session-1", "Session one draft");

      const { rerender } = render(
        <Composer onSend={mockOnSend} sessionId="session-1" />
      );

      const textarea = screen.getByPlaceholderText(
        /message/i
      ) as HTMLTextAreaElement;
      expect(textarea.value).toBe("Session one draft");

      rerender(<Composer onSend={mockOnSend} sessionId="session-2" />);

      await waitFor(() => {
        expect(textarea.value).toBe("");
      });
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels", () => {
      render(<Composer onSend={mockOnSend} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      expect(textarea).toHaveAttribute("aria-label", "Message input");

      const sendButton = screen.getByRole("button", { name: /send/i });
      expect(sendButton).toHaveAttribute("aria-label");
    });

    it("should indicate disabled state to screen readers", () => {
      render(<Composer onSend={mockOnSend} isLoading={true} />);

      const textarea = screen.getByPlaceholderText(/message/i);
      expect(textarea).toHaveAttribute("aria-disabled", "true");
    });

    it("should announce send button state changes", () => {
      render(<Composer onSend={mockOnSend} />);

      const sendButton = screen.getByRole("button", { name: /send/i });

      // Initially disabled
      expect(sendButton).toHaveAttribute("aria-disabled", "true");

      // Enable after typing
      const textarea = screen.getByPlaceholderText(/message/i);
      fireEvent.change(textarea, { target: { value: "Test" } });

      expect(sendButton).toHaveAttribute("aria-disabled", "false");
    });
  });

  describe("Keyboard shortcuts", () => {
    it("should show keyboard hint for Shift+Enter", () => {
      render(<Composer onSend={mockOnSend} />);

      // Text is split across elements, so check for both parts
      expect(screen.getByText("Shift + Enter")).toBeInTheDocument();
      expect(screen.getByText(/for new line/i)).toBeInTheDocument();
    });
  });
});

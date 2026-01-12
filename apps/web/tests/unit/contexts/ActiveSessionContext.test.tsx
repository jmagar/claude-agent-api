/**
 * ActiveSessionContext tests
 */

import { render, screen, fireEvent } from "@testing-library/react";
import {
  ActiveSessionProvider,
  useActiveSession,
} from "@/contexts/ActiveSessionContext";
import type { Message, Session } from "@/types";

function TestConsumer() {
  const {
    session,
    messages,
    isStreaming,
    setSession,
    addMessage,
    setMessages,
    clearMessages,
    setIsStreaming,
  } = useActiveSession();

  const handleSetSession = () => {
    const nextSession: Session = {
      id: "session-1",
      mode: "brainstorm",
      status: "active",
      created_at: new Date("2026-01-11T00:00:00Z"),
      updated_at: new Date("2026-01-11T00:00:00Z"),
      total_turns: 0,
      tags: [],
    };
    setSession(nextSession);
  };

  const handleAddMessage = () => {
    const message: Message = {
      id: "message-1",
      role: "user",
      content: [{ type: "text", text: "Hello" }],
      created_at: new Date("2026-01-11T00:00:00Z"),
    };
    addMessage(message);
  };

  const handleSetMessages = () => {
    const first: Message = {
      id: "message-2",
      role: "assistant",
      content: [{ type: "text", text: "First" }],
      created_at: new Date("2026-01-11T00:00:00Z"),
    };
    const second: Message = {
      id: "message-3",
      role: "assistant",
      content: [{ type: "text", text: "Second" }],
      created_at: new Date("2026-01-11T00:00:00Z"),
    };
    setMessages(() => [first, second]);
  };

  const handleAppendMessage = () => {
    const extra: Message = {
      id: "message-4",
      role: "assistant",
      content: [{ type: "text", text: "Third" }],
      created_at: new Date("2026-01-11T00:00:00Z"),
    };
    setMessages((prev) => [...prev, extra]);
  };

  return (
    <div>
      <div data-testid="session-id">{session?.id ?? "none"}</div>
      <div data-testid="message-count">{messages.length}</div>
      <div data-testid="is-streaming">{isStreaming ? "true" : "false"}</div>
      <button type="button" onClick={handleSetSession}>
        SetSession
      </button>
      <button type="button" onClick={handleAddMessage}>
        AddMessage
      </button>
      <button type="button" onClick={handleSetMessages}>
        SetMessages
      </button>
      <button type="button" onClick={handleAppendMessage}>
        AppendMessage
      </button>
      <button type="button" onClick={() => setIsStreaming(true)}>
        SetStreaming
      </button>
      <button type="button" onClick={clearMessages}>
        ClearMessages
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <ActiveSessionProvider>
      <TestConsumer />
    </ActiveSessionProvider>
  );
}

describe("ActiveSessionContext", () => {
  it("manages session and message state", () => {
    renderWithProvider();

    expect(screen.getByTestId("session-id")).toHaveTextContent("none");
    expect(screen.getByTestId("message-count")).toHaveTextContent("0");
    expect(screen.getByTestId("is-streaming")).toHaveTextContent("false");

    fireEvent.click(screen.getByText("SetSession"));
    fireEvent.click(screen.getByText("AddMessage"));
    fireEvent.click(screen.getByText("SetStreaming"));
    fireEvent.click(screen.getByText("SetMessages"));
    fireEvent.click(screen.getByText("AppendMessage"));

    expect(screen.getByTestId("session-id")).toHaveTextContent("session-1");
    expect(screen.getByTestId("message-count")).toHaveTextContent("3");
    expect(screen.getByTestId("is-streaming")).toHaveTextContent("true");

    fireEvent.click(screen.getByText("ClearMessages"));
    expect(screen.getByTestId("message-count")).toHaveTextContent("0");
  });
});

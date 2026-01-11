/**
 * Integration tests for tool execution flow
 *
 * Tests the complete flow from user prompt to tool execution visualization:
 * 1. User sends prompt requiring tool use
 * 2. Claude responds with tool_use block
 * 3. ToolCallCard appears with status "running"
 * 4. Tool executes and returns result
 * 5. ToolCallCard updates to "success" with output
 * 6. Threading lines connect parent/child tools
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { SettingsProvider } from '@/contexts/SettingsContext';
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

beforeEach(() => {
  fetchEventSourceMock.mockReset();
  // Set up default fetch mock for all API calls (tools, servers, projects, etc.)
  global.fetch = jest.fn().mockImplementation((url) => {
    // Return empty arrays for all fetch requests by default
    return Promise.resolve(
      new globalThis.Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
  });
});

function renderChatInterface() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SettingsProvider>
          <ChatInterface />
        </SettingsProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe('Tool Execution Flow', () => {
  it('displays tool call card when tool is invoked', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: { content: [{ type: "thinking", thinking: "I need to list the files in the /src directory using the ls tool." }], role: "assistant" },
      },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
      { event: "tool_result", data: { tool_use_id: "tool-abc-123", status: "running" } },
      {
        event: "tool_result",
        data: { tool_use_id: "tool-abc-123", status: "success", content: "index.ts\nutils.ts\ncomponents/", duration_ms: 45 },
      },
      {
        event: "message",
        data: { content: [{ type: "text", text: "The /src directory contains:\n- index.ts\n- utils.ts\n- components/" }], role: "assistant" },
      },
      { event: "result", data: { status: "completed", total_turns: 1 } },
    ]);
    renderChatInterface();

    // Send message requiring tool use
    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for tool call card to appear
    await waitFor(() => {
      expect(screen.getByText('Bash')).toBeInTheDocument();
    });

    // Verify tool card is present with test ID
    const toolCard = screen.getByTestId('tool-call-tool-abc-123');
    expect(toolCard).toBeInTheDocument();
  });

  it('renders threading visualization for parent-child tool calls', async () => {
    const user = userEvent.setup();
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    global.dispatchEvent(new globalThis.Event('resize'));

    mockStream([
      { event: "init", data: { session_id: "test-session-789" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-parent-1", name: "Task", input: { prompt: "Research" } },
            {
              type: "tool_use",
              id: "tool-child-1",
              name: "WebSearch",
              input: { query: "best practices" },
              parent_tool_use_id: "tool-parent-1",
            },
          ],
          role: "assistant",
        },
      },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'Research best practices');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText('Task')).toBeInTheDocument();
      expect(screen.getByText('WebSearch')).toBeInTheDocument();
    });

    const svg = screen.getByTestId('threading-svg');
    expect(svg).toBeInTheDocument();
    expect(svg.querySelectorAll('path')).toHaveLength(1);
  });

  it('shows running status during tool execution', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
      { event: "tool_result", data: { tool_use_id: "tool-abc-123", status: "running" } },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for running status
    await waitFor(() => {
      expect(screen.getByText('running')).toBeInTheDocument();
    });

    // Should show loading indicator
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('updates to success status when tool completes', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
      {
        event: "tool_result",
        data: { tool_use_id: "tool-abc-123", status: "success", content: "index.ts\nutils.ts\ncomponents/", duration_ms: 45 },
      },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for success status
    await waitFor(() => {
      expect(screen.getByText('success')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Should show output
    expect(screen.getByText(/index.ts/)).toBeInTheDocument();
    expect(screen.getByText(/utils.ts/)).toBeInTheDocument();
  });

  it('displays thinking block before tool use', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: { content: [{ type: "thinking", thinking: "I need to list the files in the /src directory using the ls tool." }], role: "assistant" },
      },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    const thinkingBlock = await screen.findByTestId('thinking-block');
    expect(thinkingBlock).toHaveAttribute('aria-expanded', 'false');
    expect(thinkingBlock).toHaveTextContent(/I need to list the files/i);
  });

  it('displays tool input when expanded', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
      { event: "tool_result", data: { tool_use_id: "tool-abc-123", status: "running" } },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for tool card to appear
    await waitFor(() => {
      expect(screen.getByText('Bash')).toBeInTheDocument();
    });

    // Expand tool card by clicking the header button
    const toolCard = screen.getByTestId('tool-call-tool-abc-123');
    const expandButton = toolCard.querySelector('button');
    expect(expandButton).toBeInTheDocument();
    await user.click(expandButton!);

    // Should show input - look for the code block with JSON content
    await waitFor(() => {
      const codeBlocks = screen.getAllByTestId('code-block');
      expect(codeBlocks.length).toBeGreaterThan(0);
      // The input should contain the command in formatted JSON
      const inputSection = screen.getByText('Input');
      expect(inputSection).toBeInTheDocument();
    });
  });

  it('displays duration after tool completes', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
      {
        event: "tool_result",
        data: { tool_use_id: "tool-abc-123", status: "success", content: "index.ts\nutils.ts\ncomponents/", duration_ms: 45 },
      },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for completion
    await waitFor(() => {
      expect(screen.getByText('success')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Should show duration
    expect(screen.getByText(/45ms/)).toBeInTheDocument();
  });

  it('renders final text response after tool execution', async () => {
    const user = userEvent.setup();
    mockStream([
      { event: "init", data: { session_id: "test-session-123" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-abc-123", name: "Bash", input: { command: "ls /src" } },
          ],
          role: "assistant",
        },
      },
      {
        event: "tool_result",
        data: { tool_use_id: "tool-abc-123", status: "success", content: "index.ts\nutils.ts\ncomponents/", duration_ms: 45 },
      },
      {
        event: "message",
        data: { content: [{ type: "text", text: "The /src directory contains:\n- index.ts\n- utils.ts\n- components/" }], role: "assistant" },
      },
    ]);
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for final response
    await waitFor(() => {
      expect(screen.getByText(/The \/src directory contains/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Both tool card and text response should be visible
    expect(screen.getByText('Bash')).toBeInTheDocument();
    expect(screen.getAllByText(/index\.ts/).length).toBeGreaterThan(0);
  });

  it('handles tool execution errors gracefully', async () => {
    mockStream([
      { event: "init", data: { session_id: "test-session-456" } },
      {
        event: "message",
        data: {
          content: [
            { type: "tool_use", id: "tool-error-1", name: "ReadFile", input: { path: "/nonexistent.txt" } },
          ],
          role: "assistant",
        },
      },
      {
        event: "tool_result",
        data: { tool_use_id: "tool-error-1", status: "error", content: "File not found: /nonexistent.txt", is_error: true },
      },
      { event: "result", data: { status: "error" } },
    ]);

    const user = userEvent.setup();
    renderChatInterface();

    const input = screen.getByPlaceholderText(/message/i);
    await user.type(input, 'Read /nonexistent.txt');
    await user.keyboard('{Enter}');

    // Wait for error status
    await waitFor(() => {
      expect(screen.getByText('error')).toBeInTheDocument();
    });

    // Should show error message
    expect(screen.getAllByText(/File not found/i).length).toBeGreaterThan(0);

    // Should show retry button
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});

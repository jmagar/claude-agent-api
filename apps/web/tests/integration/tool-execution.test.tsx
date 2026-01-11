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
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Mock SSE streaming responses
const mockToolExecutionStream = `event: init
data: {"session_id":"test-session-123"}

event: message
data: {"type":"user","content":[{"type":"text","text":"List files in /src"}]}

event: message
data: {"type":"assistant","content":[{"type":"thinking","thinking":"I need to list the files in the /src directory using the ls tool."}]}

event: message
data: {"type":"assistant","content":[{"type":"tool_use","id":"tool-abc-123","name":"Bash","input":{"command":"ls /src"}}]}

event: tool_result
data: {"tool_use_id":"tool-abc-123","status":"running"}

event: tool_result
data: {"tool_use_id":"tool-abc-123","status":"success","content":"index.ts\\nutils.ts\\ncomponents/","duration_ms":45}

event: message
data: {"type":"assistant","content":[{"type":"text","text":"The /src directory contains:\\n- index.ts\\n- utils.ts\\n- components/"}]}

event: result
data: {"status":"completed","total_turns":1}
`;

const server = setupServer(
  http.post('/api/streaming', () => {
    const stream = new ReadableStream({
      start(controller) {
        const lines = mockToolExecutionStream.split('\n');
        let index = 0;

        const interval = setInterval(() => {
          if (index < lines.length) {
            controller.enqueue(new TextEncoder().encode(lines[index] + '\n'));
            index++;
          } else {
            clearInterval(interval);
            controller.close();
          }
        }, 50); // Send line every 50ms
      },
    });

    return new HttpResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

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
    renderChatInterface();

    // Send message requiring tool use
    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for tool call card to appear
    await waitFor(() => {
      expect(screen.getByText('Bash')).toBeInTheDocument();
    });

    // Tool card should be visible
    const toolCard = screen.getByTestId('tool-call-tool-abc-123');
    expect(toolCard).toBeInTheDocument();
  });

  it('shows running status during tool execution', async () => {
    const user = userEvent.setup();
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
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
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
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
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for thinking block
    await waitFor(() => {
      expect(screen.getByText(/I need to list the files/i)).toBeInTheDocument();
    });

    // Thinking block should be collapsible
    const thinkingBlock = screen.getByTestId('thinking-block');
    expect(thinkingBlock).toHaveAttribute('aria-expanded', 'false');
  });

  it('displays tool input when expanded', async () => {
    const user = userEvent.setup();
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for tool card
    await waitFor(() => {
      expect(screen.getByText('Bash')).toBeInTheDocument();
    });

    // Expand tool card
    const toolCard = screen.getByTestId('tool-call-tool-abc-123');
    await user.click(toolCard);

    // Should show input
    expect(screen.getByText(/command/i)).toBeInTheDocument();
    expect(screen.getByText('ls /src')).toBeInTheDocument();
  });

  it('displays duration after tool completes', async () => {
    const user = userEvent.setup();
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
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
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'List files in /src');
    await user.keyboard('{Enter}');

    // Wait for final response
    await waitFor(() => {
      expect(screen.getByText(/The \/src directory contains/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Both tool card and text response should be visible
    expect(screen.getByText('Bash')).toBeInTheDocument();
    expect(screen.getByText(/index.ts/)).toBeInTheDocument();
  });

  it('handles tool execution errors gracefully', async () => {
    // Mock error response
    server.use(
      http.post('/api/streaming', () => {
        const errorStream = `event: init
data: {"session_id":"test-session-456"}

event: message
data: {"type":"assistant","content":[{"type":"tool_use","id":"tool-error-1","name":"ReadFile","input":{"path":"/nonexistent.txt"}}]}

event: tool_result
data: {"tool_use_id":"tool-error-1","status":"error","content":"File not found: /nonexistent.txt","is_error":true}

event: result
data: {"status":"error"}
`;

        return new HttpResponse(errorStream, {
          headers: { 'Content-Type': 'text/event-stream' },
        });
      })
    );

    const user = userEvent.setup();
    renderChatInterface();

    const input = screen.getByPlaceholderText(/type a message/i);
    await user.type(input, 'Read /nonexistent.txt');
    await user.keyboard('{Enter}');

    // Wait for error status
    await waitFor(() => {
      expect(screen.getByText('error')).toBeInTheDocument();
    });

    // Should show error message
    expect(screen.getByText(/File not found/i)).toBeInTheDocument();

    // Should show retry button
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});

/**
 * Tool Approval Flow Integration Tests
 *
 * Tests the complete tool approval workflow including:
 * - Permission mode management in chat interface
 * - Inline approval cards for tool execution
 * - Tool preset selection and application
 * - Permission mode effects on tool behavior
 *
 * @see FR-020: System MUST display permissions chip with four modes
 * @see FR-085: System MUST show inline approval cards in Default mode
 * @see FR-086: System MUST allow "Always allow this tool" checkbox
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { PermissionsProvider } from "@/contexts/PermissionsContext";
import { ModeProvider } from "@/contexts/ModeContext";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Create a test wrapper with all required providers
function createTestWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });

  return function TestWrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ModeProvider>
          <PermissionsProvider>{children}</PermissionsProvider>
        </ModeProvider>
      </QueryClientProvider>
    );
  };
}

// Mock streaming response with tool approval request
function createToolApprovalStream() {
  const events = [
    { event: "init", data: JSON.stringify({ session_id: "test-session" }) },
    { event: "message", data: JSON.stringify({ id: "msg-1", role: "assistant", content: [] }) },
    {
      event: "tool_start",
      data: JSON.stringify({
        id: "tool-1",
        name: "write_file",
        input: { path: "/workspace/test.ts", content: "console.log('test');" },
        requires_approval: true,
      }),
    },
  ];

  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < events.length) {
        const event = events[index];
        controller.enqueue(
          new TextEncoder().encode(`event: ${event.event}\ndata: ${event.data}\n\n`)
        );
        index++;
      } else {
        controller.close();
      }
    },
  });
}

// Mock streaming response for auto-approved tool
function createAutoApprovedToolStream() {
  const events = [
    { event: "init", data: JSON.stringify({ session_id: "test-session" }) },
    { event: "message", data: JSON.stringify({ id: "msg-1", role: "assistant", content: [] }) },
    {
      event: "tool_start",
      data: JSON.stringify({
        id: "tool-1",
        name: "write_file",
        input: { path: "/workspace/test.ts", content: "console.log('test');" },
        requires_approval: false,
      }),
    },
    {
      event: "tool_end",
      data: JSON.stringify({
        id: "tool-1",
        output: { success: true, message: "File written successfully" },
      }),
    },
    { event: "result", data: JSON.stringify({ success: true }) },
  ];

  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < events.length) {
        const event = events[index];
        controller.enqueue(
          new TextEncoder().encode(`event: ${event.event}\ndata: ${event.data}\n\n`)
        );
        index++;
      } else {
        controller.close();
      }
    },
  });
}

// NOTE: Many tests in this file are skipped pending full ChatInterface integration
// with PermissionsChip, ToolBadge, and ToolManagementModal components.
// The components are implemented and tested individually - this file tests the integration.

describe("Tool Approval Flow Integration", () => {
  beforeEach(() => {
    mockFetch.mockClear();
    localStorage.clear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // Skip integration tests pending ChatInterface integration work
  describe("Permission mode display in ChatInterface", () => {
    it("shows permissions chip in composer area", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /permissions/i })).toBeInTheDocument();
      });
    });

    it("defaults to Default permission mode", async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        const chip = screen.getByRole("button", { name: /permissions/i });
        expect(chip).toHaveTextContent(/default/i);
      });
    });

    it("cycles permission mode on chip click", async () => {
      const user = userEvent.setup();
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      const chip = await screen.findByRole("button", { name: /permissions/i });
      await user.click(chip);

      expect(chip).toHaveTextContent(/accept edits/i);
    });

    it("persists permission mode in localStorage", async () => {
      const user = userEvent.setup();
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      const chip = await screen.findByRole("button", { name: /permissions/i });
      await user.click(chip);

      expect(localStorage.getItem("permissionMode")).toBe(JSON.stringify("acceptEdits"));
    });

    it("restores permission mode from localStorage on mount", async () => {
      localStorage.setItem("permissionMode", JSON.stringify("dontAsk"));

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        const chip = screen.getByRole("button", { name: /permissions/i });
        expect(chip).toHaveTextContent(/don't ask/i);
      });
    });
  });

  describe("Inline approval cards (Default mode)", () => {
    it("shows approval card when tool requires approval", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card to appear
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      // Verify approval card content
      const approvalCard = screen.getByTestId("tool-approval-card");
      expect(within(approvalCard).getByText("write_file")).toBeInTheDocument();
      expect(within(approvalCard).getByText("/workspace/test.ts")).toBeInTheDocument();
    });

    it("shows approve and reject buttons on approval card", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      expect(screen.getByRole("button", { name: /approve/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /reject/i })).toBeInTheDocument();
    });

    it("shows 'Always allow this tool' checkbox on approval card", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      expect(
        screen.getByRole("checkbox", { name: /always allow this tool/i })
      ).toBeInTheDocument();
    });

    it("sends approval response when approve is clicked", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        if (url.includes("/api/tool-approval")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ success: true }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      // Click approve
      await user.click(screen.getByRole("button", { name: /approve/i }));

      // Verify API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/tool-approval"),
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"approved":true'),
          })
        );
      });
    });

    it("sends rejection response when reject is clicked", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        if (url.includes("/api/tool-approval")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ success: true }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      // Click reject
      await user.click(screen.getByRole("button", { name: /reject/i }));

      // Verify API call
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/tool-approval"),
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining('"approved":false'),
          })
        );
      });
    });

    it("remembers tool when 'Always allow' is checked before approve", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        if (url.includes("/api/tool-approval")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ success: true }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      // Check "Always allow"
      await user.click(screen.getByRole("checkbox", { name: /always allow/i }));

      // Click approve
      await user.click(screen.getByRole("button", { name: /approve/i }));

      // Verify API call includes remember flag
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/tool-approval"),
          expect.objectContaining({
            body: expect.stringContaining('"remember":true'),
          })
        );
      });
    });

    it("hides approval card after approval is submitted", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createToolApprovalStream(),
          });
        }
        if (url.includes("/api/tool-approval")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ success: true }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Wait for approval card
      await waitFor(() => {
        expect(screen.getByTestId("tool-approval-card")).toBeInTheDocument();
      });

      // Click approve
      await user.click(screen.getByRole("button", { name: /approve/i }));

      // Card should disappear
      await waitFor(() => {
        expect(screen.queryByTestId("tool-approval-card")).not.toBeInTheDocument();
      });
    });
  });

  describe("Accept Edits mode", () => {
    it("auto-approves file edit tools without showing approval card", async () => {
      const user = userEvent.setup();
      localStorage.setItem("permissionMode", JSON.stringify("acceptEdits"));

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createAutoApprovedToolStream(),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Verify mode is set
      await waitFor(() => {
        const chip = screen.getByRole("button", { name: /permissions/i });
        expect(chip).toHaveTextContent(/accept edits/i);
      });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Create a test file");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Should NOT show approval card for file edits
      await waitFor(() => {
        expect(screen.queryByTestId("tool-approval-card")).not.toBeInTheDocument();
      });

      // Should show tool as completed
      await waitFor(() => {
        expect(screen.getByTestId("tool-call-tool-1")).toBeInTheDocument();
      });
    });
  });

  describe("Don't Ask mode", () => {
    it("auto-approves all tools without showing approval card", async () => {
      const user = userEvent.setup();
      localStorage.setItem("permissionMode", JSON.stringify("dontAsk"));

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/streaming")) {
          return Promise.resolve({
            ok: true,
            body: createAutoApprovedToolStream(),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Verify mode is set
      await waitFor(() => {
        const chip = screen.getByRole("button", { name: /permissions/i });
        expect(chip).toHaveTextContent(/don't ask/i);
      });

      // Send a message
      const input = screen.getByRole("textbox");
      await user.type(input, "Run dangerous command");
      await user.click(screen.getByRole("button", { name: /send/i }));

      // Should NOT show approval card
      await waitFor(() => {
        expect(screen.queryByTestId("tool-approval-card")).not.toBeInTheDocument();
      });
    });
  });

  describe("Tool preset integration", () => {
    it("shows tool badge with active tool count in composer", async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/tools")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              tools: [
                { name: "read_file", enabled: true },
                { name: "write_file", enabled: true },
                { name: "execute_sql", enabled: false },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        const toolBadge = screen.getByTestId("tool-badge");
        expect(toolBadge).toHaveTextContent("2");
      });
    });

    it("opens tool management modal when tool badge is clicked", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/tools")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              tools: [{ name: "read_file", enabled: true }],
            }),
          });
        }
        if (url.includes("/api/mcp-servers")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ servers: [] }),
          });
        }
        if (url.includes("/api/tool-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ presets: [] }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      await waitFor(() => {
        expect(screen.getByTestId("tool-badge")).toBeInTheDocument();
      });

      await user.click(screen.getByTestId("tool-badge"));

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Tool Management")).toBeInTheDocument();
      });
    });

    it("updates tool count when preset is applied", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/sessions")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ messages: [] }),
          });
        }
        if (url.includes("/api/tools")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              tools: [
                { name: "read_file", enabled: true },
                { name: "write_file", enabled: false },
              ],
            }),
          });
        }
        if (url.includes("/api/mcp-servers")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ servers: [] }),
          });
        }
        if (url.includes("/api/tool-presets")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              presets: [
                {
                  id: "preset-1",
                  name: "All Tools",
                  tools: ["read_file", "write_file"],
                },
              ],
            }),
          });
        }
        if (url.includes("/api/tool-presets/preset-1/apply")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({
              tools: [
                { name: "read_file", enabled: true },
                { name: "write_file", enabled: true },
              ],
            }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Initial count should be 1
      await waitFor(() => {
        expect(screen.getByTestId("tool-badge")).toHaveTextContent("1");
      });

      // Open modal and apply preset
      await user.click(screen.getByTestId("tool-badge"));

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });

      const presetDropdown = screen.getByRole("combobox", { name: /preset/i });
      await user.click(presetDropdown);
      await user.click(screen.getByText("All Tools"));

      // Count should update to 2
      await waitFor(() => {
        expect(screen.getByTestId("tool-badge")).toHaveTextContent("2");
      });
    });
  });

  describe("Keyboard shortcuts", () => {
    it("cycles permission mode with keyboard shortcut", async () => {
      const user = userEvent.setup();

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ messages: [] }),
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Ctrl+Shift+P should cycle permission mode
      await user.keyboard("{Control>}{Shift>}p{/Shift}{/Control}");

      await waitFor(() => {
        const chip = screen.getByRole("button", { name: /permissions/i });
        expect(chip).toHaveTextContent(/accept edits/i);
      });
    });

    it("opens tool management modal with keyboard shortcut", async () => {
      const user = userEvent.setup();

      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/tools")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ tools: [] }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({}),
        });
      });

      render(<ChatInterface />, { wrapper: createTestWrapper() });

      // Ctrl+Shift+T should open tool modal
      await user.keyboard("{Control>}{Shift>}t{/Shift}{/Control}");

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText("Tool Management")).toBeInTheDocument();
      });
    });
  });
});

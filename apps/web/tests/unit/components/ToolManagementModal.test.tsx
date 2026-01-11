/**
 * ToolManagementModal Component Tests
 *
 * Tests the tool management modal that allows users to:
 * - View tools grouped by MCP server
 * - Enable/disable individual tools
 * - Save and load tool presets
 * - Search and filter tools
 *
 * @see FR-017: System MUST show tool management modal with tools grouped by MCP server
 * @see FR-018: System MUST allow enabling/disabling individual tools
 * @see FR-019: System MUST support saving tool configurations as named presets
 * @see FR-033: System MUST display MCP tools grouped by server
 */

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ToolManagementModal } from "@/components/modals/ToolManagementModal";
import type { ToolDefinition, ToolPreset, McpServerConfig } from "@/types";

// Mock data
const mockTools: ToolDefinition[] = [
  {
    name: "read_file",
    description: "Read contents of a file",
    input_schema: { type: "object", properties: { path: { type: "string" } } },
    server: "filesystem",
    enabled: true,
  },
  {
    name: "write_file",
    description: "Write contents to a file",
    input_schema: { type: "object", properties: { path: { type: "string" } } },
    server: "filesystem",
    enabled: true,
  },
  {
    name: "execute_sql",
    description: "Execute SQL query",
    input_schema: { type: "object", properties: { query: { type: "string" } } },
    server: "database",
    enabled: false,
  },
  {
    name: "web_search",
    description: "Search the web",
    input_schema: { type: "object", properties: { query: { type: "string" } } },
    server: "web",
    enabled: true,
  },
];

const mockServers: McpServerConfig[] = [
  {
    id: "srv-1",
    name: "filesystem",
    type: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-filesystem"],
    enabled: true,
    status: "active",
    created_at: new Date("2026-01-01"),
    updated_at: new Date("2026-01-01"),
    tools_count: 2,
  },
  {
    id: "srv-2",
    name: "database",
    type: "stdio",
    command: "npx",
    args: ["-y", "@modelcontextprotocol/server-postgres"],
    enabled: true,
    status: "active",
    created_at: new Date("2026-01-01"),
    updated_at: new Date("2026-01-01"),
    tools_count: 1,
  },
  {
    id: "srv-3",
    name: "web",
    type: "sse",
    url: "https://mcp.example.com/web",
    enabled: true,
    status: "active",
    created_at: new Date("2026-01-01"),
    updated_at: new Date("2026-01-01"),
    tools_count: 1,
  },
];

const mockPresets: ToolPreset[] = [
  {
    id: "preset-1",
    name: "Development",
    description: "Tools for development",
    tools: ["read_file", "write_file"],
    created_at: new Date("2026-01-01"),
    is_default: true,
  },
  {
    id: "preset-2",
    name: "Read Only",
    description: "Read-only access",
    tools: ["read_file"],
    created_at: new Date("2026-01-01"),
  },
];

describe("ToolManagementModal", () => {
  const defaultProps = {
    open: true,
    onClose: jest.fn(),
    tools: mockTools,
    servers: mockServers,
    presets: mockPresets,
    onToolToggle: jest.fn(),
    onPresetSelect: jest.fn(),
    onPresetCreate: jest.fn(),
    onPresetDelete: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Modal behavior", () => {
    it("renders when open is true", () => {
      render(<ToolManagementModal {...defaultProps} />);
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Tool Management")).toBeInTheDocument();
    });

    it("does not render when open is false", () => {
      render(<ToolManagementModal {...defaultProps} open={false} />);
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("calls onClose when close button is clicked", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const closeButton = screen.getByRole("button", { name: /close/i });
      await user.click(closeButton);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it("calls onClose when clicking backdrop", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const backdrop = screen.getByTestId("modal-backdrop");
      await user.click(backdrop);

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it("calls onClose when pressing Escape", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      await user.keyboard("{Escape}");

      expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe("Tool grouping by server (FR-017, FR-033)", () => {
    it("groups tools by MCP server", () => {
      render(<ToolManagementModal {...defaultProps} />);

      // Should show server headers
      expect(screen.getByText("filesystem")).toBeInTheDocument();
      expect(screen.getByText("database")).toBeInTheDocument();
      expect(screen.getByText("web")).toBeInTheDocument();
    });

    it("shows tool count per server in header", () => {
      render(<ToolManagementModal {...defaultProps} />);

      // Each server header should show tool count
      const filesystemHeader = screen.getByText("filesystem").closest("[data-server-group]");
      expect(filesystemHeader).toHaveTextContent("2 tools");

      const databaseHeader = screen.getByText("database").closest("[data-server-group]");
      expect(databaseHeader).toHaveTextContent("1 tool");
    });

    it("shows server status indicator", () => {
      render(<ToolManagementModal {...defaultProps} />);

      // Active servers should show green indicator
      const filesystemGroup = screen.getByTestId("server-group-filesystem");
      expect(within(filesystemGroup).getByTestId("status-indicator")).toHaveClass("bg-green-500");
    });

    it("shows tools under their respective server groups", () => {
      render(<ToolManagementModal {...defaultProps} />);

      const filesystemGroup = screen.getByTestId("server-group-filesystem");
      expect(within(filesystemGroup).getByText("read_file")).toBeInTheDocument();
      expect(within(filesystemGroup).getByText("write_file")).toBeInTheDocument();

      const databaseGroup = screen.getByTestId("server-group-database");
      expect(within(databaseGroup).getByText("execute_sql")).toBeInTheDocument();
    });

    it("collapses and expands server groups", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const filesystemHeader = screen.getByTestId("server-header-filesystem");

      // Initially expanded - tools visible
      expect(screen.getByText("read_file")).toBeInTheDocument();

      // Click to collapse - tools removed from DOM
      await user.click(filesystemHeader);
      expect(screen.queryByText("read_file")).not.toBeInTheDocument();

      // Click to expand - tools back in DOM
      await user.click(filesystemHeader);
      expect(screen.getByText("read_file")).toBeInTheDocument();
    });
  });

  describe("Tool toggle (FR-018)", () => {
    it("shows toggle switch for each tool", () => {
      render(<ToolManagementModal {...defaultProps} />);

      const toggles = screen.getAllByRole("switch");
      expect(toggles).toHaveLength(mockTools.length);
    });

    it("shows enabled state correctly", () => {
      render(<ToolManagementModal {...defaultProps} />);

      const readFileToggle = screen.getByRole("switch", { name: /read_file/i });
      const executeSqlToggle = screen.getByRole("switch", { name: /execute_sql/i });

      expect(readFileToggle).toBeChecked();
      expect(executeSqlToggle).not.toBeChecked();
    });

    it("calls onToolToggle when tool is toggled", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const readFileToggle = screen.getByRole("switch", { name: /read_file/i });
      await user.click(readFileToggle);

      expect(defaultProps.onToolToggle).toHaveBeenCalledWith("read_file", false);
    });

    it("shows tool description on hover or focus", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const readFileTool = screen.getByTestId("tool-item-read_file");
      await user.hover(readFileTool);

      expect(screen.getByText("Read contents of a file")).toBeInTheDocument();
    });

    it("allows toggling all tools in a server group", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const toggleAllFilesystem = screen.getByRole("checkbox", { name: /toggle all filesystem/i });
      await user.click(toggleAllFilesystem);

      // Should toggle all tools in filesystem group
      expect(defaultProps.onToolToggle).toHaveBeenCalledWith("read_file", false);
      expect(defaultProps.onToolToggle).toHaveBeenCalledWith("write_file", false);
    });
  });

  describe("Tool presets (FR-019)", () => {
    it("shows preset dropdown", () => {
      render(<ToolManagementModal {...defaultProps} />);

      expect(screen.getByRole("combobox", { name: /preset/i })).toBeInTheDocument();
    });

    it("lists available presets in dropdown", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const presetDropdown = screen.getByRole("combobox", { name: /preset/i });
      await user.click(presetDropdown);

      expect(screen.getByText("Development")).toBeInTheDocument();
      expect(screen.getByText("Read Only")).toBeInTheDocument();
    });

    it("shows default preset indicator", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const presetDropdown = screen.getByRole("combobox", { name: /preset/i });
      await user.click(presetDropdown);

      const developmentOption = screen.getByText("Development").closest("[role='option']");
      expect(developmentOption).toHaveTextContent("Default");
    });

    it("calls onPresetSelect when preset is selected", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const presetDropdown = screen.getByRole("combobox", { name: /preset/i });
      await user.click(presetDropdown);
      await user.click(screen.getByText("Read Only"));

      expect(defaultProps.onPresetSelect).toHaveBeenCalledWith(mockPresets[1]);
    });

    it("shows save preset button", () => {
      render(<ToolManagementModal {...defaultProps} />);

      expect(screen.getByRole("button", { name: /save.*preset/i })).toBeInTheDocument();
    });

    it("opens save preset dialog when save button clicked", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const saveButton = screen.getByRole("button", { name: /save.*preset/i });
      await user.click(saveButton);

      expect(screen.getByRole("dialog", { name: /save preset/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/preset name/i)).toBeInTheDocument();
    });

    it("calls onPresetCreate with name and tools when preset saved", async () => {
      const user = userEvent.setup({ delay: null });
      render(<ToolManagementModal {...defaultProps} />);

      // Open save dialog
      await user.click(screen.getByRole("button", { name: /save.*preset/i }));

      // Enter name
      const nameInput = screen.getByLabelText(/preset name/i);
      await user.clear(nameInput);
      await user.type(nameInput, "My Custom Preset");

      // Save
      await user.click(screen.getByRole("button", { name: /^save$/i }));

      expect(defaultProps.onPresetCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "My Custom Preset",
          tools: ["read_file", "write_file", "web_search"], // Currently enabled tools
        })
      );
    });

    it("shows delete button for non-default presets", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const presetDropdown = screen.getByRole("combobox", { name: /preset/i });
      await user.click(presetDropdown);

      // Select a non-default preset
      await user.click(screen.getByText("Read Only"));

      // Should show delete button
      expect(screen.getByRole("button", { name: /delete.*preset/i })).toBeInTheDocument();
    });

    it("calls onPresetDelete when delete is confirmed", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      // Select preset first
      const presetDropdown = screen.getByRole("combobox", { name: /preset/i });
      await user.click(presetDropdown);
      await user.click(screen.getByText("Read Only"));

      // Click delete
      await user.click(screen.getByRole("button", { name: /delete.*preset/i }));

      // Confirm deletion
      await user.click(screen.getByRole("button", { name: /confirm/i }));

      expect(defaultProps.onPresetDelete).toHaveBeenCalledWith("preset-2");
    });
  });

  describe("Search and filter", () => {
    it("shows search input", () => {
      render(<ToolManagementModal {...defaultProps} />);

      expect(screen.getByRole("searchbox", { name: /search tools/i })).toBeInTheDocument();
    });

    it("filters tools by name when searching", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const searchInput = screen.getByRole("searchbox", { name: /search tools/i });
      await user.type(searchInput, "file");

      // Should show matching tools
      expect(screen.getByText("read_file")).toBeInTheDocument();
      expect(screen.getByText("write_file")).toBeInTheDocument();

      // Should not show non-matching tools
      expect(screen.queryByText("execute_sql")).not.toBeInTheDocument();
      expect(screen.queryByText("web_search")).not.toBeInTheDocument();
    });

    it("filters tools by description when searching", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const searchInput = screen.getByRole("searchbox", { name: /search tools/i });
      await user.type(searchInput, "SQL");

      expect(screen.getByText("execute_sql")).toBeInTheDocument();
      expect(screen.queryByText("read_file")).not.toBeInTheDocument();
    });

    it("shows empty state when no tools match search", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const searchInput = screen.getByRole("searchbox", { name: /search tools/i });
      await user.type(searchInput, "nonexistent");

      expect(screen.getByText(/no tools found/i)).toBeInTheDocument();
    });

    it("clears search when clear button clicked", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const searchInput = screen.getByRole("searchbox", { name: /search tools/i });
      await user.type(searchInput, "file");

      const clearButton = screen.getByRole("button", { name: /clear search/i });
      await user.click(clearButton);

      expect(searchInput).toHaveValue("");
      expect(screen.getByText("execute_sql")).toBeInTheDocument();
    });

    it("shows filter by enabled state toggle", () => {
      render(<ToolManagementModal {...defaultProps} />);

      expect(screen.getByRole("checkbox", { name: /show enabled only/i })).toBeInTheDocument();
    });

    it("filters to show only enabled tools when checked", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const enabledOnlyToggle = screen.getByRole("checkbox", { name: /show enabled only/i });
      await user.click(enabledOnlyToggle);

      expect(screen.getByText("read_file")).toBeInTheDocument();
      expect(screen.queryByText("execute_sql")).not.toBeInTheDocument(); // disabled tool
    });
  });

  describe("Tool count summary", () => {
    it("shows total and enabled tool counts", () => {
      render(<ToolManagementModal {...defaultProps} />);

      expect(screen.getByText(/3 of 4 tools enabled/i)).toBeInTheDocument();
    });

    it("updates count when tools are toggled", async () => {
      const user = userEvent.setup();
      const { rerender } = render(<ToolManagementModal {...defaultProps} />);

      // Toggle a tool off
      const readFileToggle = screen.getByRole("switch", { name: /read_file/i });
      await user.click(readFileToggle);

      // Simulate parent updating tools prop
      const updatedTools = mockTools.map((t) =>
        t.name === "read_file" ? { ...t, enabled: false } : t
      );
      rerender(<ToolManagementModal {...defaultProps} tools={updatedTools} />);

      expect(screen.getByText(/2 of 4 tools enabled/i)).toBeInTheDocument();
    });
  });

  describe("Loading and error states", () => {
    it("shows loading skeleton when isLoading is true", () => {
      render(<ToolManagementModal {...defaultProps} isLoading={true} />);

      expect(screen.getByTestId("tool-modal-loading")).toBeInTheDocument();
    });

    it("shows error message when error is provided", () => {
      render(<ToolManagementModal {...defaultProps} error="Failed to load tools" />);

      expect(screen.getByText("Failed to load tools")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    });

    it("calls onRetry when retry button clicked", async () => {
      const onRetry = jest.fn();
      const user = userEvent.setup();
      render(
        <ToolManagementModal
          {...defaultProps}
          error="Failed to load tools"
          onRetry={onRetry}
        />
      );

      await user.click(screen.getByRole("button", { name: /retry/i }));

      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("traps focus within modal when open", async () => {
      const user = userEvent.setup();
      render(<ToolManagementModal {...defaultProps} />);

      const closeButton = screen.getByRole("button", { name: /close/i });
      closeButton.focus();

      // Tab through all focusable elements and verify focus stays in modal
      await user.tab();
      expect(document.activeElement).not.toBe(document.body);
      expect(screen.getByRole("dialog").contains(document.activeElement)).toBe(true);
    });

    it("has proper ARIA attributes", () => {
      render(<ToolManagementModal {...defaultProps} />);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute("aria-labelledby");
    });

    it("tool toggles have accessible labels", () => {
      render(<ToolManagementModal {...defaultProps} />);

      const toggles = screen.getAllByRole("switch");
      toggles.forEach((toggle) => {
        expect(toggle).toHaveAccessibleName();
      });
    });
  });
});

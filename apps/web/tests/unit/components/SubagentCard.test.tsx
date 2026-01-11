/**
 * Unit tests for SubagentCard component
 *
 * Tests the dedicated subagent visualization card with:
 * - Collapse/expand functionality
 * - Status display and icons
 * - Progress indicators
 * - Child tool calls display
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { SubagentCard } from "@/components/chat/SubagentCard";
import type { ToolCall } from "@/types";

describe("SubagentCard", () => {
  const defaultProps = {
    id: "subagent-1",
    type: "Explore",
    status: "running" as const,
  };

  describe("rendering", () => {
    it("should render with correct testid", () => {
      render(<SubagentCard {...defaultProps} />);

      expect(screen.getByTestId("subagent-subagent-1")).toBeInTheDocument();
    });

    it("should display subagent type", () => {
      render(<SubagentCard {...defaultProps} />);

      expect(screen.getByText("Explore")).toBeInTheDocument();
    });

    it("should display status badge", () => {
      render(<SubagentCard {...defaultProps} status="success" />);

      expect(screen.getByText("success")).toBeInTheDocument();
    });

    it("should be collapsed by default", () => {
      render(<SubagentCard {...defaultProps} description="Test description" />);

      // Description should not be visible when collapsed
      expect(screen.queryByText('"Test description"')).not.toBeInTheDocument();
    });
  });

  describe("collapse/expand", () => {
    it("should expand when header is clicked", () => {
      render(<SubagentCard {...defaultProps} description="Test description" />);

      const header = screen.getByRole("button");
      fireEvent.click(header);

      expect(screen.getByText('"Test description"')).toBeInTheDocument();
    });

    it("should collapse when header is clicked again", () => {
      render(<SubagentCard {...defaultProps} description="Test description" />);

      const header = screen.getByRole("button");
      fireEvent.click(header); // Expand
      fireEvent.click(header); // Collapse

      expect(screen.queryByText('"Test description"')).not.toBeInTheDocument();
    });

    it("should respect external collapsed prop", () => {
      render(
        <SubagentCard
          {...defaultProps}
          collapsed={false}
          description="Test description"
        />
      );

      expect(screen.getByText('"Test description"')).toBeInTheDocument();
    });

    it("should call onToggle when header is clicked", () => {
      const onToggle = jest.fn();
      render(<SubagentCard {...defaultProps} onToggle={onToggle} />);

      const header = screen.getByRole("button");
      fireEvent.click(header);

      expect(onToggle).toHaveBeenCalled();
    });

    it("should auto-expand on error status", () => {
      const { rerender } = render(<SubagentCard {...defaultProps} />);

      // Initially collapsed
      expect(screen.getByRole("button")).toHaveAttribute("aria-expanded", "false");

      // Rerender with error status
      rerender(<SubagentCard {...defaultProps} status="error" description="Error occurred" />);

      // Should auto-expand
      expect(screen.getByText('"Error occurred"')).toBeInTheDocument();
    });
  });

  describe("status display", () => {
    it("should show loading spinner for running status", () => {
      render(<SubagentCard {...defaultProps} status="running" />);

      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("should show success icon for success status", () => {
      render(<SubagentCard {...defaultProps} status="success" />);

      expect(screen.getByText("success")).toBeInTheDocument();
    });

    it("should show error icon for error status", () => {
      render(<SubagentCard {...defaultProps} status="error" />);

      expect(screen.getByText("error")).toBeInTheDocument();
    });
  });

  describe("duration display", () => {
    it("should display duration in milliseconds for short durations", () => {
      render(<SubagentCard {...defaultProps} duration_ms={500} />);

      expect(screen.getByText("500ms")).toBeInTheDocument();
    });

    it("should display duration in seconds for medium durations", () => {
      render(<SubagentCard {...defaultProps} duration_ms={2500} />);

      expect(screen.getByText("2.5s")).toBeInTheDocument();
    });

    it("should display duration in minutes for long durations", () => {
      render(<SubagentCard {...defaultProps} duration_ms={120000} />);

      expect(screen.getByText("2.0m")).toBeInTheDocument();
    });

    it("should not display duration if not provided", () => {
      render(<SubagentCard {...defaultProps} />);

      expect(screen.queryByText(/ms|s$/)).not.toBeInTheDocument();
    });
  });

  describe("token usage display", () => {
    it("should display token usage when provided", () => {
      render(
        <SubagentCard {...defaultProps} tokenUsage={{ input: 100, output: 200 }} />
      );

      expect(screen.getByText("300 tokens")).toBeInTheDocument();
    });

    it("should display token usage in k format for large numbers", () => {
      render(
        <SubagentCard {...defaultProps} tokenUsage={{ input: 5000, output: 5000 }} />
      );

      expect(screen.getByText("10.0k tokens")).toBeInTheDocument();
    });
  });

  describe("tool calls display", () => {
    const childToolCalls: ToolCall[] = [
      { id: "tool-1", name: "read_file", status: "success", input: {} },
      { id: "tool-2", name: "write_file", status: "running", input: {} },
      { id: "tool-3", name: "bash", status: "idle", input: {} },
    ];

    it("should display tool count", () => {
      render(<SubagentCard {...defaultProps} childToolCalls={childToolCalls} />);

      expect(screen.getByText("1/3 tools")).toBeInTheDocument();
    });

    it("should display total count when no running tools", () => {
      const completedTools: ToolCall[] = [
        { id: "tool-1", name: "read_file", status: "success", input: {} },
        { id: "tool-2", name: "write_file", status: "success", input: {} },
      ];

      render(<SubagentCard {...defaultProps} childToolCalls={completedTools} />);

      expect(screen.getByText("2 tools")).toBeInTheDocument();
    });

    it("should show progress bar when running with tools", () => {
      render(
        <SubagentCard
          {...defaultProps}
          status="running"
          childToolCalls={childToolCalls}
          collapsed={false}
        />
      );

      expect(screen.getByText("Progress")).toBeInTheDocument();
      expect(screen.getByText("1/3")).toBeInTheDocument();
    });
  });

  describe("children rendering", () => {
    it("should render children when expanded", () => {
      render(
        <SubagentCard {...defaultProps} collapsed={false}>
          <div data-testid="child-content">Child content</div>
        </SubagentCard>
      );

      expect(screen.getByTestId("child-content")).toBeInTheDocument();
    });

    it("should not render children when collapsed", () => {
      render(
        <SubagentCard {...defaultProps} collapsed={true}>
          <div data-testid="child-content">Child content</div>
        </SubagentCard>
      );

      expect(screen.queryByTestId("child-content")).not.toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("should have aria-expanded attribute on header button", () => {
      render(<SubagentCard {...defaultProps} />);

      const header = screen.getByRole("button");
      expect(header).toHaveAttribute("aria-expanded", "false");
    });

    it("should update aria-expanded when expanded", () => {
      render(<SubagentCard {...defaultProps} collapsed={false} />);

      const header = screen.getByRole("button");
      expect(header).toHaveAttribute("aria-expanded", "true");
    });
  });
});

/**
 * Unit tests for ModeToggle component
 *
 * Tests the mode toggle button that switches between Brainstorm and Code modes:
 * - FR-013: Show mode toggle button in sidebar to switch between modes
 * - FR-015: Preserve mode preference in localStorage per session
 *
 * RED PHASE: These tests are written first and MUST FAIL
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { ModeToggle } from "@/components/sidebar/ModeToggle";
import type { SessionMode } from "@/types";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

beforeEach(() => {
  localStorageMock.clear();
  jest.clearAllMocks();
});

describe("ModeToggle", () => {
  describe("rendering", () => {
    it("should render the mode toggle button", () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      expect(screen.getByRole("button")).toBeInTheDocument();
    });

    it("should display current mode label", () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      expect(screen.getByText(/brainstorm/i)).toBeInTheDocument();
    });

    it("should have accessible name for the toggle", () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      expect(
        screen.getByRole("button", { name: /toggle mode|switch mode/i })
      ).toBeInTheDocument();
    });

    it("should show brainstorm icon when in brainstorm mode", () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      expect(screen.getByTestId("brainstorm-icon")).toBeInTheDocument();
    });

    it("should show code icon when in code mode", () => {
      render(<ModeToggle mode="code" onModeChange={jest.fn()} />);

      expect(screen.getByTestId("code-icon")).toBeInTheDocument();
    });
  });

  describe("mode switching", () => {
    it("should call onModeChange when clicked", () => {
      const onModeChange = jest.fn();
      render(<ModeToggle mode="brainstorm" onModeChange={onModeChange} />);

      fireEvent.click(screen.getByRole("button"));

      expect(onModeChange).toHaveBeenCalledTimes(1);
    });

    it("should request code mode when currently in brainstorm mode", () => {
      const onModeChange = jest.fn();
      render(<ModeToggle mode="brainstorm" onModeChange={onModeChange} />);

      fireEvent.click(screen.getByRole("button"));

      expect(onModeChange).toHaveBeenCalledWith("code");
    });

    it("should request brainstorm mode when currently in code mode", () => {
      const onModeChange = jest.fn();
      render(<ModeToggle mode="code" onModeChange={onModeChange} />);

      fireEvent.click(screen.getByRole("button"));

      expect(onModeChange).toHaveBeenCalledWith("brainstorm");
    });
  });

  describe("visual states", () => {
    it("should apply active styles for brainstorm mode", () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-yellow-100");
    });

    it("should apply active styles for code mode", () => {
      render(<ModeToggle mode="code" onModeChange={jest.fn()} />);

      const button = screen.getByRole("button");
      expect(button).toHaveClass("bg-blue-100");
    });

    it("should show tooltip on hover", async () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      const button = screen.getByRole("button");
      fireEvent.mouseEnter(button);

      expect(await screen.findByRole("tooltip")).toBeInTheDocument();
      expect(screen.getByText(/click to switch to code mode/i)).toBeInTheDocument();
    });
  });

  describe("keyboard navigation", () => {
    it("should be focusable", () => {
      render(<ModeToggle mode="brainstorm" onModeChange={jest.fn()} />);

      const button = screen.getByRole("button");
      button.focus();

      expect(button).toHaveFocus();
    });

    it("should trigger on Enter key", () => {
      const onModeChange = jest.fn();
      render(<ModeToggle mode="brainstorm" onModeChange={onModeChange} />);

      const button = screen.getByRole("button");
      fireEvent.keyDown(button, { key: "Enter" });

      expect(onModeChange).toHaveBeenCalled();
    });

    it("should trigger on Space key", () => {
      const onModeChange = jest.fn();
      render(<ModeToggle mode="brainstorm" onModeChange={onModeChange} />);

      const button = screen.getByRole("button");
      fireEvent.keyDown(button, { key: " " });

      expect(onModeChange).toHaveBeenCalled();
    });
  });

  describe("disabled state", () => {
    it("should not call onModeChange when disabled", () => {
      const onModeChange = jest.fn();
      render(
        <ModeToggle mode="brainstorm" onModeChange={onModeChange} disabled />
      );

      fireEvent.click(screen.getByRole("button"));

      expect(onModeChange).not.toHaveBeenCalled();
    });

    it("should show disabled styling", () => {
      render(
        <ModeToggle mode="brainstorm" onModeChange={jest.fn()} disabled />
      );

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
      expect(button).toHaveClass("opacity-50");
    });
  });
});

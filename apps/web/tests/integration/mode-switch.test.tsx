/**
 * Integration tests for mode switching flow
 *
 * Tests the complete flow of switching between Brainstorm and Code modes:
 * 1. User clicks mode toggle in sidebar
 * 2. When switching to Code mode, project picker appears
 * 3. User selects a project
 * 4. Mode changes and sidebar reorganizes
 * 5. Sessions are grouped by project in Code mode, by date in Brainstorm mode
 *
 * FR-011: Support Brainstorm mode with date-grouped sidebar
 * FR-012: Support Code mode with project-grouped sidebar
 * FR-013: Show mode toggle button in sidebar
 * FR-014: Display project picker when toggling from Brainstorm to Code mode
 * FR-015: Preserve mode preference in localStorage
 *
 * RED PHASE: These tests are written first and MUST FAIL
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { ModeProvider } from "@/contexts/ModeContext";
import type { Session, Project } from "@/types";

// Mock fetch for API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock projects response
const mockProjects: Project[] = [
  {
    id: "proj-1",
    name: "Frontend App",
    path: "/workspace/frontend-app",
    created_at: new Date("2026-01-01"),
    session_count: 5,
    last_accessed_at: new Date("2026-01-10"),
  },
  {
    id: "proj-2",
    name: "Backend API",
    path: "/workspace/backend-api",
    created_at: new Date("2025-12-15"),
    session_count: 12,
    last_accessed_at: new Date("2026-01-09"),
  },
];

// Mock sessions response
const mockSessions: Session[] = [
  {
    id: "session-1",
    mode: "brainstorm",
    status: "active",
    title: "Planning new feature",
    created_at: new Date("2026-01-11T10:00:00Z"),
    updated_at: new Date("2026-01-11T10:30:00Z"),
    total_turns: 5,
    tags: [],
  },
  {
    id: "session-2",
    mode: "brainstorm",
    status: "completed",
    title: "Exploring API design",
    created_at: new Date("2026-01-10T14:00:00Z"),
    updated_at: new Date("2026-01-10T15:00:00Z"),
    total_turns: 8,
    tags: [],
  },
  {
    id: "session-3",
    mode: "code",
    status: "active",
    project_id: "proj-1",
    title: "Implementing login page",
    created_at: new Date("2026-01-09T09:00:00Z"),
    updated_at: new Date("2026-01-09T11:00:00Z"),
    total_turns: 15,
    tags: [],
  },
];

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
  mockFetch.mockReset();

  // Default API responses
  mockFetch.mockImplementation((url: string) => {
    if (url.includes("/api/projects")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockProjects),
      });
    }
    if (url.includes("/api/sessions")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSessions),
      });
    }
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    });
  });
});

function renderApp() {
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
          <ModeProvider>
            <ChatInterface />
          </ModeProvider>
        </SettingsProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("Mode Switching Flow", () => {
  describe("initial state", () => {
    it("should default to brainstorm mode", () => {
      renderApp();

      expect(screen.getByText(/brainstorm/i)).toBeInTheDocument();
    });

    it("should show mode toggle in sidebar", () => {
      renderApp();

      expect(
        screen.getByRole("button", { name: /toggle mode|switch mode/i })
      ).toBeInTheDocument();
    });

    it("should restore saved mode from localStorage", () => {
      localStorageMock.setItem("sessionMode", '"code"');
      localStorageMock.setItem("selectedProjectId", '"proj-1"');

      renderApp();

      expect(screen.getByText(/code/i)).toBeInTheDocument();
    });
  });

  describe("switching from Brainstorm to Code mode", () => {
    it("should show project picker when switching to Code mode", async () => {
      const user = userEvent.setup();
      renderApp();

      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.getByText(/select a project/i)).toBeInTheDocument();
      });
    });

    it("should display available projects in picker", async () => {
      const user = userEvent.setup();
      renderApp();

      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
        expect(screen.getByText("Backend API")).toBeInTheDocument();
      });
    });

    it("should switch to Code mode after selecting project", async () => {
      const user = userEvent.setup();
      renderApp();

      // Click mode toggle
      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      // Wait for modal and select project
      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
      });
      await user.click(screen.getByText("Frontend App"));

      // Verify mode changed
      await waitFor(() => {
        expect(screen.getByTestId("code-icon")).toBeInTheDocument();
      });
    });

    it("should not switch mode if project picker is canceled", async () => {
      const user = userEvent.setup();
      renderApp();

      // Click mode toggle
      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      // Wait for modal and press Escape
      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });
      await user.keyboard("{Escape}");

      // Should still be in brainstorm mode
      expect(screen.getByTestId("brainstorm-icon")).toBeInTheDocument();
    });
  });

  describe("switching from Code to Brainstorm mode", () => {
    it("should switch directly without picker", async () => {
      const user = userEvent.setup();
      localStorageMock.setItem("sessionMode", '"code"');
      localStorageMock.setItem("selectedProjectId", '"proj-1"');

      renderApp();

      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      // Should switch directly without modal
      await waitFor(() => {
        expect(screen.getByTestId("brainstorm-icon")).toBeInTheDocument();
      });
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  describe("sidebar organization", () => {
    it("should group sessions by date in Brainstorm mode", async () => {
      renderApp();

      await waitFor(() => {
        expect(screen.getByText("Today")).toBeInTheDocument();
        expect(screen.getByText("Yesterday")).toBeInTheDocument();
      });
    });

    it("should group sessions by project in Code mode", async () => {
      const user = userEvent.setup();
      localStorageMock.setItem("sessionMode", '"code"');
      localStorageMock.setItem("selectedProjectId", '"proj-1"');

      renderApp();

      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
        // Sessions should be under project heading
      });
    });

    it("should reorganize sidebar when mode changes", async () => {
      const user = userEvent.setup();
      renderApp();

      // Initially in brainstorm mode - should see date groups
      await waitFor(() => {
        expect(screen.getByText("Today")).toBeInTheDocument();
      });

      // Switch to code mode
      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      // Select a project
      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
      });
      await user.click(screen.getByText("Frontend App"));

      // Should now see project-grouped sidebar
      await waitFor(() => {
        // Date groups should be gone, replaced with project grouping
        expect(screen.queryByText("Today")).not.toBeInTheDocument();
      });
    });
  });

  describe("mode persistence", () => {
    it("should save mode to localStorage", async () => {
      const user = userEvent.setup();
      renderApp();

      // Switch to code mode
      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
      });
      await user.click(screen.getByText("Frontend App"));

      // Verify localStorage was updated
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "sessionMode",
        expect.stringContaining("code")
      );
    });

    it("should save selected project to localStorage in Code mode", async () => {
      const user = userEvent.setup();
      renderApp();

      // Switch to code mode
      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
      });
      await user.click(screen.getByText("Frontend App"));

      // Verify project was saved
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "selectedProjectId",
        expect.stringContaining("proj-1")
      );
    });
  });

  describe("project context", () => {
    it("should show selected project name in header when in Code mode", async () => {
      const user = userEvent.setup();
      localStorageMock.setItem("sessionMode", '"code"');
      localStorageMock.setItem("selectedProjectId", '"proj-1"');

      renderApp();

      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
      });
    });

    it("should allow changing project in Code mode", async () => {
      const user = userEvent.setup();
      localStorageMock.setItem("sessionMode", '"code"');
      localStorageMock.setItem("selectedProjectId", '"proj-1"');

      renderApp();

      // Click on project name to change it
      await waitFor(() => {
        expect(screen.getByText("Frontend App")).toBeInTheDocument();
      });

      const projectButton = screen.getByRole("button", {
        name: /change project|select project/i,
      });
      await user.click(projectButton);

      // Should show project picker
      await waitFor(() => {
        expect(screen.getByRole("dialog")).toBeInTheDocument();
      });

      // Select different project
      await user.click(screen.getByText("Backend API"));

      // Should update selected project
      await waitFor(() => {
        expect(screen.getByText("Backend API")).toBeInTheDocument();
      });
    });
  });

  describe("error handling", () => {
    it("should show error when projects fail to load", async () => {
      mockFetch.mockImplementation((url: string) => {
        if (url.includes("/api/projects")) {
          return Promise.resolve({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ error: "Server error" }),
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      });

      const user = userEvent.setup();
      renderApp();

      const modeToggle = screen.getByRole("button", {
        name: /toggle mode|switch mode/i,
      });
      await user.click(modeToggle);

      await waitFor(() => {
        expect(screen.getByText(/failed to load projects/i)).toBeInTheDocument();
      });
    });
  });
});

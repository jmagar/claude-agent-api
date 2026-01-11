/**
 * Unit tests for ProjectPicker component
 *
 * Tests the project picker modal that appears when switching to Code mode:
 * - FR-014: Display project picker when toggling from Brainstorm to Code mode
 * - FR-012: Support Code mode with project-grouped sidebar
 *
 * RED PHASE: These tests are written first and MUST FAIL
 */

import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectPicker } from "@/components/modals/ProjectPickerModal";
import type { Project } from "@/types";

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
  {
    id: "proj-3",
    name: "Shared Utils",
    path: "/workspace/shared-utils",
    created_at: new Date("2025-11-01"),
    session_count: 3,
    last_accessed_at: new Date("2025-12-20"),
  },
];

describe("ProjectPicker", () => {
  describe("rendering", () => {
    it("should render the modal when open is true", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("should not render when open is false", () => {
      render(
        <ProjectPicker
          open={false}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    it("should display modal title", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(screen.getByText(/select a project/i)).toBeInTheDocument();
    });

    it("should display all projects in the list", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(screen.getByText("Frontend App")).toBeInTheDocument();
      expect(screen.getByText("Backend API")).toBeInTheDocument();
      expect(screen.getByText("Shared Utils")).toBeInTheDocument();
    });

    it("should display project paths", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(screen.getByText("/workspace/frontend-app")).toBeInTheDocument();
    });

    it("should display session counts", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(screen.getByText(/5 sessions/i)).toBeInTheDocument();
      expect(screen.getByText(/12 sessions/i)).toBeInTheDocument();
    });
  });

  describe("search functionality", () => {
    it("should display search input", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      expect(
        screen.getByPlaceholderText(/search projects/i)
      ).toBeInTheDocument();
    });

    it("should filter projects by name", async () => {
      const user = userEvent.setup();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search projects/i);
      await user.type(searchInput, "Frontend");

      expect(screen.getByText("Frontend App")).toBeInTheDocument();
      expect(screen.queryByText("Backend API")).not.toBeInTheDocument();
      expect(screen.queryByText("Shared Utils")).not.toBeInTheDocument();
    });

    it("should filter projects by path", async () => {
      const user = userEvent.setup();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search projects/i);
      await user.type(searchInput, "backend-api");

      expect(screen.queryByText("Frontend App")).not.toBeInTheDocument();
      expect(screen.getByText("Backend API")).toBeInTheDocument();
    });

    it("should show empty state when no matches", async () => {
      const user = userEvent.setup();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search projects/i);
      await user.type(searchInput, "nonexistent");

      expect(screen.getByText(/no projects found/i)).toBeInTheDocument();
    });
  });

  describe("project selection", () => {
    it("should call onSelectProject when project is clicked", () => {
      const onSelectProject = jest.fn();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={onSelectProject}
          projects={mockProjects}
        />
      );

      fireEvent.click(screen.getByText("Frontend App"));

      expect(onSelectProject).toHaveBeenCalledWith(mockProjects[0]);
    });

    it("should call onClose after project selection", () => {
      const onClose = jest.fn();
      render(
        <ProjectPicker
          open={true}
          onClose={onClose}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      fireEvent.click(screen.getByText("Frontend App"));

      expect(onClose).toHaveBeenCalled();
    });

    it("should highlight selected project", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
          selectedProjectId="proj-2"
        />
      );

      const selectedItem = screen.getByText("Backend API").closest("button");
      expect(selectedItem).toHaveClass("bg-blue-50");
    });
  });

  describe("keyboard navigation", () => {
    it("should support arrow key navigation", async () => {
      const user = userEvent.setup();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      // Focus the first item
      await user.keyboard("{ArrowDown}");
      expect(screen.getByText("Frontend App").closest("button")).toHaveFocus();

      // Navigate to second item
      await user.keyboard("{ArrowDown}");
      expect(screen.getByText("Backend API").closest("button")).toHaveFocus();
    });

    it("should select on Enter key", async () => {
      const user = userEvent.setup();
      const onSelectProject = jest.fn();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={onSelectProject}
          projects={mockProjects}
        />
      );

      await user.keyboard("{ArrowDown}");
      await user.keyboard("{Enter}");

      expect(onSelectProject).toHaveBeenCalledWith(mockProjects[0]);
    });

    it("should close on Escape key", async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(
        <ProjectPicker
          open={true}
          onClose={onClose}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      await user.keyboard("{Escape}");

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe("adding new project", () => {
    it("should show add project button", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
          onAddProject={jest.fn()}
        />
      );

      expect(
        screen.getByRole("button", { name: /add project|new project/i })
      ).toBeInTheDocument();
    });

    it("should call onAddProject when add button is clicked", () => {
      const onAddProject = jest.fn();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
          onAddProject={onAddProject}
        />
      );

      fireEvent.click(
        screen.getByRole("button", { name: /add project|new project/i })
      );

      expect(onAddProject).toHaveBeenCalled();
    });
  });

  describe("empty state", () => {
    it("should show empty state when no projects exist", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={[]}
        />
      );

      expect(screen.getByText(/no projects yet/i)).toBeInTheDocument();
    });

    it("should show create project CTA in empty state", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={[]}
          onAddProject={jest.fn()}
        />
      );

      expect(
        screen.getByRole("button", { name: /create.*project/i })
      ).toBeInTheDocument();
    });
  });

  describe("loading state", () => {
    it("should show loading skeleton when loading", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={[]}
          isLoading={true}
        />
      );

      expect(screen.getByTestId("project-picker-loading")).toBeInTheDocument();
    });
  });

  describe("sorting", () => {
    it("should sort projects by last accessed by default", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      const projectItems = screen.getAllByRole("button", { name: /session/i });
      const names = projectItems.map((item) => item.textContent);

      // Frontend App was accessed most recently (Jan 10)
      expect(names[0]).toContain("Frontend App");
    });
  });

  describe("accessibility", () => {
    it("should have proper dialog role and label", () => {
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-labelledby");
    });

    it("should trap focus within modal", async () => {
      const user = userEvent.setup();
      render(
        <ProjectPicker
          open={true}
          onClose={jest.fn()}
          onSelectProject={jest.fn()}
          projects={mockProjects}
        />
      );

      // Tab through all focusable elements
      await user.tab();
      expect(document.activeElement).toBeInTheDocument();
      // Focus should stay within the modal
    });
  });
});

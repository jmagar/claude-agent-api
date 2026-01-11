"use client";

import { useState, useCallback, useRef, useEffect, memo, useMemo } from "react";
import { X, Plus, FolderOpen, Search } from "lucide-react";
import type { Project } from "@/types";

export interface ProjectPickerProps {
  open: boolean;
  onClose: () => void;
  onSelectProject: (project: Project) => void;
  projects: Project[];
  selectedProjectId?: string;
  onAddProject?: () => void;
  isLoading?: boolean;
}

export const ProjectPicker = memo(function ProjectPicker({
  open,
  onClose,
  onSelectProject,
  projects,
  selectedProjectId,
  onAddProject,
  isLoading = false,
}: ProjectPickerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Sort projects by last accessed date (most recent first)
  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      const dateA = a.last_accessed_at ? new Date(a.last_accessed_at).getTime() : 0;
      const dateB = b.last_accessed_at ? new Date(b.last_accessed_at).getTime() : 0;
      return dateB - dateA;
    });
  }, [projects]);

  // Filter projects based on search query
  const filteredProjects = useMemo(() => {
    if (!searchQuery.trim()) return sortedProjects;
    const query = searchQuery.toLowerCase();
    return sortedProjects.filter(
      (project) =>
        project.name.toLowerCase().includes(query) ||
        project.path.toLowerCase().includes(query)
    );
  }, [sortedProjects, searchQuery]);

  // Focus search input when modal opens
  useEffect(() => {
    if (open && searchInputRef.current) {
      searchInputRef.current.focus();
    }
    if (!open) {
      setSearchQuery("");
      setFocusedIndex(-1);
    }
  }, [open]);

  const handleSelectProject = useCallback(
    (project: Project) => {
      onSelectProject(project);
      onClose();
    },
    [onSelectProject, onClose]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "Escape":
          onClose();
          break;
        case "ArrowDown":
          e.preventDefault();
          setFocusedIndex((prev) =>
            prev < filteredProjects.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case "Enter":
          e.preventDefault();
          if (focusedIndex >= 0 && focusedIndex < filteredProjects.length) {
            handleSelectProject(filteredProjects[focusedIndex]);
          }
          break;
      }
    },
    [onClose, filteredProjects, focusedIndex, handleSelectProject]
  );

  // Scroll focused item into view
  useEffect(() => {
    if (focusedIndex >= 0 && listRef.current) {
      const buttons = listRef.current.querySelectorAll("button[data-project]");
      if (buttons[focusedIndex]) {
        (buttons[focusedIndex] as HTMLButtonElement).focus();
      }
    }
  }, [focusedIndex]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
      onKeyDown={handleKeyDown}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="project-picker-title"
        className="relative w-full max-w-lg rounded-12 bg-white p-24 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-16 flex items-center justify-between">
          <h2 id="project-picker-title" className="text-18 font-semibold">
            Select a Project
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-6 p-4 hover:bg-gray-100"
          >
            <X className="h-20 w-20" />
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-16">
          <Search className="absolute left-12 top-1/2 h-16 w-16 -translate-y-1/2 text-gray-400" />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-8 border border-gray-300 py-10 pl-40 pr-12 text-14 focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Loading State */}
        {isLoading && (
          <div data-testid="project-picker-loading" className="space-y-12">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-64 animate-pulse rounded-8 bg-gray-100"
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && projects.length === 0 && (
          <div className="py-32 text-center">
            <FolderOpen className="mx-auto mb-8 h-48 w-48 text-gray-300" />
            <p className="text-14 text-gray-500">No projects yet</p>
            {onAddProject && (
              <button
                type="button"
                onClick={onAddProject}
                className="mt-16 rounded-8 bg-blue-600 px-16 py-8 text-14 font-medium text-white hover:bg-blue-700"
              >
                Create your first project
              </button>
            )}
          </div>
        )}

        {/* No Search Results */}
        {!isLoading &&
          projects.length > 0 &&
          filteredProjects.length === 0 && (
            <div className="py-32 text-center">
              <p className="text-14 text-gray-500">No projects found</p>
            </div>
          )}

        {/* Project List */}
        {!isLoading && filteredProjects.length > 0 && (
          <div ref={listRef} className="max-h-[300px] space-y-8 overflow-y-auto">
            {filteredProjects.map((project, index) => (
              <button
                key={project.id}
                type="button"
                data-project={project.id}
                onClick={() => handleSelectProject(project)}
                aria-label={`${project.name} - ${project.session_count} sessions`}
                className={`
                  flex w-full items-start gap-12 rounded-8 p-12 text-left transition-colors
                  ${selectedProjectId === project.id ? "bg-blue-50 ring-2 ring-blue-500" : "hover:bg-gray-50"}
                  ${focusedIndex === index ? "bg-gray-100" : ""}
                `}
              >
                <FolderOpen className="mt-2 h-20 w-20 flex-shrink-0 text-blue-500" />
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-gray-900">{project.name}</div>
                  <div className="truncate text-12 text-gray-500">
                    {project.path}
                  </div>
                  <div className="text-12 text-gray-400">
                    {project.session_count} sessions
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Add Project Button */}
        {onAddProject && projects.length > 0 && (
          <div className="mt-16 border-t pt-16">
            <button
              type="button"
              onClick={onAddProject}
              aria-label="Add project"
              className="flex w-full items-center justify-center gap-8 rounded-8 border border-dashed border-gray-300 py-12 text-14 text-gray-600 hover:border-gray-400 hover:bg-gray-50"
            >
              <Plus className="h-16 w-16" />
              Add Project
            </button>
          </div>
        )}
      </div>
    </div>
  );
});

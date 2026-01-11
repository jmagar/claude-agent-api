/**
 * ModeContext - Manages the application mode state (Brainstorm vs Code)
 *
 * Provides:
 * - Current mode (brainstorm or code)
 * - Selected project information for Code mode
 * - Mode persistence to localStorage
 * - Project picker modal state
 *
 * @see FR-011: Brainstorm mode with date-grouped sidebar
 * @see FR-012: Code mode with project-grouped sidebar
 * @see FR-015: Preserve mode preference in localStorage
 */

"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import type { SessionMode, Project } from "@/types";

/** Context value type for mode management */
export interface ModeContextType {
  /** Current mode - determines sidebar organization */
  mode: SessionMode;
  /** Selected project ID for Code mode */
  selectedProjectId: string | null;
  /** Full project object for selected project */
  selectedProject: Project | null;
  /** Update the current mode and persist to localStorage */
  setMode: (mode: SessionMode) => void;
  /** Update the selected project ID and persist to localStorage */
  setSelectedProjectId: (projectId: string | null) => void;
  /** Update the selected project object */
  setSelectedProject: (project: Project | null) => void;
  /** Whether the project picker modal is visible */
  showProjectPicker: boolean;
  /** Control project picker modal visibility */
  setShowProjectPicker: (show: boolean) => void;
}

const ModeContext = createContext<ModeContextType | undefined>(undefined);

/** localStorage key for mode persistence */
const MODE_STORAGE_KEY = "sessionMode";
/** localStorage key for selected project persistence */
const PROJECT_STORAGE_KEY = "selectedProjectId";

export function ModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<SessionMode>("brainstorm");
  const [selectedProjectId, setSelectedProjectIdState] = useState<string | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showProjectPicker, setShowProjectPicker] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const storedMode = localStorage.getItem(MODE_STORAGE_KEY);
      const storedProjectId = localStorage.getItem(PROJECT_STORAGE_KEY);

      if (storedMode) {
        const parsedMode = JSON.parse(storedMode) as SessionMode;
        if (parsedMode === "brainstorm" || parsedMode === "code") {
          setModeState(parsedMode);
        }
      }

      if (storedProjectId) {
        const parsedProjectId = JSON.parse(storedProjectId) as string;
        setSelectedProjectIdState(parsedProjectId);
      }
    } catch {
      // Invalid JSON, use defaults
    }
    setIsHydrated(true);
  }, []);

  const setMode = useCallback((newMode: SessionMode) => {
    setModeState(newMode);
    localStorage.setItem(MODE_STORAGE_KEY, JSON.stringify(newMode));
  }, []);

  const setSelectedProjectId = useCallback((projectId: string | null) => {
    setSelectedProjectIdState(projectId);
    if (projectId) {
      localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(projectId));
    } else {
      localStorage.removeItem(PROJECT_STORAGE_KEY);
    }
  }, []);

  // Don't render until hydrated to prevent hydration mismatch
  if (!isHydrated) {
    return null;
  }

  return (
    <ModeContext.Provider
      value={{
        mode,
        selectedProjectId,
        selectedProject,
        setMode,
        setSelectedProjectId,
        setSelectedProject,
        showProjectPicker,
        setShowProjectPicker,
      }}
    >
      {children}
    </ModeContext.Provider>
  );
}

export function useMode() {
  const context = useContext(ModeContext);
  if (!context) {
    throw new Error("useMode must be used within a ModeProvider");
  }
  return context;
}

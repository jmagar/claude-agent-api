"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import type { ThemeMode, ThreadingMode, PermissionMode } from "@/types";

interface Settings {
  theme: ThemeMode;
  threadingMode: ThreadingMode;
  workspaceBaseDir: string;
  defaultPermissionMode: PermissionMode;
  defaultModel: string;
  autoCompactThreshold: number;
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (partial: Partial<Settings>) => void;
  toggleTheme: () => void;
}

const defaultSettings: Settings = {
  theme: "system",
  threadingMode: "auto",
  workspaceBaseDir: "/workspaces",
  defaultPermissionMode: "default",
  defaultModel: "sonnet",
  autoCompactThreshold: 100,
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(defaultSettings);

  useEffect(() => {
    // Load settings from localStorage
    const stored = localStorage.getItem("settings");
    if (stored) {
      try {
        setSettings({ ...defaultSettings, ...JSON.parse(stored) });
      } catch {
        // Invalid JSON, use defaults
      }
    }

    // Apply theme class to document
    applyTheme(settings.theme);
  }, []);

  const applyTheme = (theme: ThemeMode) => {
    const root = document.documentElement;

    if (theme === "system") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.classList.toggle("dark", prefersDark);
    } else {
      root.classList.toggle("dark", theme === "dark");
    }
  };

  const updateSettings = (partial: Partial<Settings>) => {
    const newSettings = { ...settings, ...partial };
    setSettings(newSettings);
    localStorage.setItem("settings", JSON.stringify(newSettings));

    if (partial.theme) {
      applyTheme(partial.theme);
    }
  };

  const toggleTheme = () => {
    const newTheme: ThemeMode = settings.theme === "light" ? "dark" : "light";
    updateSettings({ theme: newTheme });
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, toggleTheme }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}

/**
 * SettingsContext tests
 *
 * Validates settings defaults and per-setting setter behavior.
 */

import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { SettingsProvider, useSettings } from "@/contexts/SettingsContext";
import type { PermissionMode, ThreadingMode } from "@/types";

function TestConsumer() {
  const {
    theme,
    threadingMode,
    defaultPermissionMode,
    workspaceBaseDir,
    messageDensity,
    showTimestamps,
    setTheme,
    toggleTheme,
    setThreadingMode,
    setDefaultPermissionMode,
    setWorkspaceBaseDir,
    setMessageDensity,
    toggleShowTimestamps,
  } = useSettings();

  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="threadingMode">{threadingMode}</div>
      <div data-testid="defaultPermissionMode">{defaultPermissionMode}</div>
      <div data-testid="workspaceBaseDir">{workspaceBaseDir}</div>
      <div data-testid="messageDensity">{messageDensity}</div>
      <div data-testid="showTimestamps">{showTimestamps ? "true" : "false"}</div>

      <button type="button" onClick={() => setTheme("dark")}>SetTheme</button>
      <button type="button" onClick={toggleTheme}>ToggleTheme</button>
      <button
        type="button"
        onClick={() => setThreadingMode("hover" as ThreadingMode)}
      >
        SetThreading
      </button>
      <button
        type="button"
        onClick={() => setDefaultPermissionMode("dontAsk" as PermissionMode)}
      >
        SetPermission
      </button>
      <button
        type="button"
        onClick={() => setWorkspaceBaseDir("/workspace")}
      >
        SetWorkspace
      </button>
      <button
        type="button"
        onClick={() => setMessageDensity("compact")}
      >
        SetDensity
      </button>
      <button type="button" onClick={toggleShowTimestamps}>
        ToggleTimestamps
      </button>
    </div>
  );
}

function renderWithProvider() {
  return render(
    <SettingsProvider>
      <TestConsumer />
    </SettingsProvider>
  );
}

describe("SettingsContext", () => {
  beforeEach(() => {
    cleanup();
    jest.clearAllMocks();
    const store = new Map<string, string>();
    localStorage.getItem = jest.fn((key: string) => store.get(key) ?? null);
    localStorage.setItem = jest.fn((key: string, value: string) => {
      store.set(key, value);
    });
    localStorage.removeItem = jest.fn((key: string) => {
      store.delete(key);
    });
    localStorage.clear = jest.fn(() => {
      store.clear();
    });
  });

  afterEach(() => {
    cleanup();
  });

  it("exposes default settings", () => {
    renderWithProvider();

    expect(screen.getByTestId("theme")).toHaveTextContent("light");
    expect(screen.getByTestId("threadingMode")).toHaveTextContent("adaptive");
    expect(screen.getByTestId("defaultPermissionMode")).toHaveTextContent("default");
    expect(screen.getByTestId("workspaceBaseDir")).toHaveTextContent("/workspaces");
    expect(screen.getByTestId("messageDensity")).toHaveTextContent("comfortable");
    expect(screen.getByTestId("showTimestamps")).toHaveTextContent("true");
  });

  it("updates settings via setters", () => {
    renderWithProvider();

    fireEvent.click(screen.getByText("SetTheme"));
    fireEvent.click(screen.getByText("SetThreading"));
    fireEvent.click(screen.getByText("SetPermission"));
    fireEvent.click(screen.getByText("SetWorkspace"));
    fireEvent.click(screen.getByText("SetDensity"));
    fireEvent.click(screen.getByText("ToggleTimestamps"));

    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    expect(screen.getByTestId("threadingMode")).toHaveTextContent("hover");
    expect(screen.getByTestId("defaultPermissionMode")).toHaveTextContent("dontAsk");
    expect(screen.getByTestId("workspaceBaseDir")).toHaveTextContent("/workspace");
    expect(screen.getByTestId("messageDensity")).toHaveTextContent("compact");
    expect(screen.getByTestId("showTimestamps")).toHaveTextContent("false");
  });

  it("toggles theme between light and dark", async () => {
    renderWithProvider();

    fireEvent.click(screen.getByText("ToggleTheme"));
    await waitFor(() =>
      expect(screen.getByTestId("theme")).toHaveTextContent("dark")
    );

    fireEvent.click(screen.getByText("ToggleTheme"));
    await waitFor(() =>
      expect(screen.getByTestId("theme")).toHaveTextContent("light")
    );
  });
});

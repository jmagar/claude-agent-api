/**
 * SettingsContext tests
 *
 * Validates settings defaults and per-setting setter behavior.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { SettingsProvider, useSettings } from "@/contexts/SettingsContext";
import type { PermissionMode, ThreadingMode } from "@/types";

function TestConsumer() {
  const {
    theme,
    threadingMode,
    defaultPermissionMode,
    workspaceBaseDir,
    messageDensity,
    defaultModel,
    autoCompactThreshold,
    showTimestamps,
    setTheme,
    toggleTheme,
    setThreadingMode,
    setDefaultPermissionMode,
    setWorkspaceBaseDir,
    setMessageDensity,
    setDefaultModel,
    setAutoCompactThreshold,
    toggleShowTimestamps,
  } = useSettings();

  return (
    <div>
      <div data-testid="theme">{theme}</div>
      <div data-testid="threadingMode">{threadingMode}</div>
      <div data-testid="defaultPermissionMode">{defaultPermissionMode}</div>
      <div data-testid="workspaceBaseDir">{workspaceBaseDir}</div>
      <div data-testid="messageDensity">{messageDensity}</div>
      <div data-testid="defaultModel">{defaultModel}</div>
      <div data-testid="autoCompactThreshold">{autoCompactThreshold}</div>
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
      <button
        type="button"
        onClick={() => setDefaultModel("opus")}
      >
        SetModel
      </button>
      <button
        type="button"
        onClick={() => setAutoCompactThreshold(200)}
      >
        SetThreshold
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
    jest.clearAllMocks();
    localStorage.getItem = jest.fn().mockReturnValue(null);
  });

  it("exposes default settings", () => {
    renderWithProvider();

    expect(screen.getByTestId("theme")).toHaveTextContent("system");
    expect(screen.getByTestId("threadingMode")).toHaveTextContent("adaptive");
    expect(screen.getByTestId("defaultPermissionMode")).toHaveTextContent("default");
    expect(screen.getByTestId("workspaceBaseDir")).toHaveTextContent("/workspaces");
    expect(screen.getByTestId("messageDensity")).toHaveTextContent("comfortable");
    expect(screen.getByTestId("defaultModel")).toHaveTextContent("sonnet");
    expect(screen.getByTestId("autoCompactThreshold")).toHaveTextContent("100");
    expect(screen.getByTestId("showTimestamps")).toHaveTextContent("true");
  });

  it("updates settings via setters", () => {
    renderWithProvider();

    fireEvent.click(screen.getByText("SetTheme"));
    fireEvent.click(screen.getByText("SetThreading"));
    fireEvent.click(screen.getByText("SetPermission"));
    fireEvent.click(screen.getByText("SetWorkspace"));
    fireEvent.click(screen.getByText("SetDensity"));
    fireEvent.click(screen.getByText("SetModel"));
    fireEvent.click(screen.getByText("SetThreshold"));
    fireEvent.click(screen.getByText("ToggleTimestamps"));

    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    expect(screen.getByTestId("threadingMode")).toHaveTextContent("hover");
    expect(screen.getByTestId("defaultPermissionMode")).toHaveTextContent("dontAsk");
    expect(screen.getByTestId("workspaceBaseDir")).toHaveTextContent("/workspace");
    expect(screen.getByTestId("messageDensity")).toHaveTextContent("compact");
    expect(screen.getByTestId("defaultModel")).toHaveTextContent("opus");
    expect(screen.getByTestId("autoCompactThreshold")).toHaveTextContent("200");
    expect(screen.getByTestId("showTimestamps")).toHaveTextContent("false");
  });

  it("toggles theme between light and dark", () => {
    renderWithProvider();

    fireEvent.click(screen.getByText("ToggleTheme"));
    expect(screen.getByTestId("theme")).toHaveTextContent("light");

    fireEvent.click(screen.getByText("ToggleTheme"));
    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
  });
});

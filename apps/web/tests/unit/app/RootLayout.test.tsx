/**
 * RootLayout provider tests
 */

import { render, screen } from "@testing-library/react";
import { AppProviders } from "@/components/app/app-providers";
import { useActiveSession } from "@/contexts/ActiveSessionContext";
import { useModeOptional } from "@/contexts/ModeContext";
import { usePermissionsOptional } from "@/contexts/PermissionsContext";

function ContextConsumer() {
  const activeSession = useActiveSession();
  const mode = useModeOptional();
  const permissions = usePermissionsOptional();

  return (
    <div>
      <div data-testid="active-session">
        {activeSession ? "present" : "missing"}
      </div>
      <div data-testid="mode-context">{mode ? "present" : "missing"}</div>
      <div data-testid="permissions-context">
        {permissions ? "present" : "missing"}
      </div>
    </div>
  );
}

describe("AppProviders", () => {
  it("provides required context providers", async () => {
    render(
      <AppProviders>
        <ContextConsumer />
      </AppProviders>
    );

    expect(await screen.findByTestId("active-session")).toHaveTextContent(
      "present"
    );
    expect(screen.getByTestId("mode-context")).toHaveTextContent("present");
    expect(screen.getByTestId("permissions-context")).toHaveTextContent(
      "present"
    );
  });
});

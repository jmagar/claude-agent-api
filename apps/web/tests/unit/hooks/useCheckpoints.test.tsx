/**
 * useCheckpoints hook tests
 */

import { render, screen, waitFor } from "@/tests/utils/test-utils";
import { useCheckpoints } from "@/hooks/useCheckpoints";

function TestComponent({ sessionId }: { sessionId: string }) {
  const { checkpoints, isLoading, error } = useCheckpoints(sessionId);

  if (isLoading) {
    return <div data-testid="loading">Loading</div>;
  }

  if (error) {
    return <div data-testid="error">{error}</div>;
  }

  return (
    <div data-testid="count">
      {checkpoints ? checkpoints.length : 0}
    </div>
  );
}

describe("useCheckpoints", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        checkpoints: [
          {
            id: "checkpoint-1",
            session_id: "session-1",
            user_message_uuid: "uuid-1",
            created_at: "2026-01-11T02:00:00Z",
            files_modified: [],
          },
        ],
      }),
    }) as jest.Mock;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("returns checkpoints for a session", async () => {
    render(<TestComponent sessionId="session-1" />);

    await waitFor(() => {
      expect(screen.getByTestId("count")).toHaveTextContent("1");
    });
  });
});

/**
 * query key factory tests
 */

import { queryKeys } from "@/lib/query-keys";

describe("queryKeys", () => {
  it("builds session checkpoint keys", () => {
    expect(queryKeys.sessions.checkpoints("session-1")).toEqual([
      "sessions",
      "detail",
      "session-1",
      "checkpoints",
    ]);
  });
});

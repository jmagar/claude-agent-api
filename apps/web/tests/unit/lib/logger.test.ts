/**
 * Logger utility tests
 */

import { logger } from "@/lib/logger";

describe("logger", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it("formats timestamps in EST with required format", () => {
    jest.setSystemTime(new Date("2026-01-11T12:34:56Z"));

    const logSpy = jest.spyOn(console, "log").mockImplementation(() => undefined);

    logger.info("Test message");

    expect(logSpy).toHaveBeenCalledTimes(1);
    const payload = JSON.parse(String(logSpy.mock.calls[0]?.[0]));

    expect(payload.timestamp).toBe("07:34:56 | 01/11/2026");
    expect(payload.level).toBe("info");
    expect(payload.message).toBe("Test message");
  });
});

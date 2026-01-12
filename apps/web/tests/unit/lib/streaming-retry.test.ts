/**
 * streaming retry delay tests
 */

import { calculateRetryDelay, defaultRetryConfig } from "@/lib/streaming-retry";

describe("calculateRetryDelay", () => {
  it("uses exponential backoff with jitter", () => {
    const config = { ...defaultRetryConfig, initialDelay: 100, backoffFactor: 2 };

    expect(calculateRetryDelay(0, config, () => 0)).toBe(100);
    expect(calculateRetryDelay(1, config, () => 0)).toBe(200);
    expect(calculateRetryDelay(2, config, () => 0)).toBe(400);
    expect(calculateRetryDelay(1, config, () => 1)).toBe(260);
  });

  it("caps delay at maxDelay", () => {
    const config = { ...defaultRetryConfig, initialDelay: 10000, maxDelay: 15000 };

    expect(calculateRetryDelay(3, config, () => 0)).toBe(15000);
  });
});

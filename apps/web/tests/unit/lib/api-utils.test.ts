/**
 * API utility tests
 */

import { NextRequest } from "next/server";
import { checkRateLimit, errorResponse, getApiKey } from "@/lib/api-utils";

describe("api-utils", () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  it("formats error responses with code and message", async () => {
    const response = errorResponse("VALIDATION_ERROR", "Missing name", 400, {
      field: "name",
    });

    expect(response.status).toBe(400);
    const body = await response.json();
    expect(body).toEqual({
      code: "VALIDATION_ERROR",
      message: "Missing name",
      details: { field: "name" },
    });
  });

  it("extracts API key from headers", () => {
    const request = new NextRequest("http://localhost/api/test", {
      headers: { "x-api-key": "test-key" },
    });

    expect(getApiKey(request)).toBe("test-key");
  });

  it("enforces rate limits", () => {
    jest.useFakeTimers().setSystemTime(new Date("2026-01-11T00:00:00Z"));

    const first = checkRateLimit("client-1", 1, 1000);
    expect(first.allowed).toBe(true);

    const second = checkRateLimit("client-1", 1, 1000);
    expect(second.allowed).toBe(false);
    expect(second.retryAfterMs).toBeGreaterThan(0);
  });
});

/**
 * Tool approval BFF route tests
 */

import type { NextRequest } from "next/server";

const mockFetch = jest.fn();

global.fetch = mockFetch as typeof fetch;

function buildRequest(
  body: Record<string, unknown>,
  headers?: Record<string, string>
) {
  return {
    headers: new Headers({
      "Content-Type": "application/json",
      ...(headers ?? {}),
    }),
    cookies: {
      get: () => undefined,
    },
    json: async () => body,
  } as unknown as NextRequest;
}

describe("POST /api/tool-approval", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = "http://backend/api/v1";
    jest.resetModules();
  });

  it("returns 401 when API key is missing", async () => {
    const { POST } = await import("@/app/api/tool-approval/route");
    const request = buildRequest({ tool_use_id: "tool-1", approved: true });

    const response = await POST(request);

    expect(response.status).toBe(401);
  });

  it("proxies approval request to backend", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    const { POST } = await import("@/app/api/tool-approval/route");
    const request = buildRequest(
      { tool_use_id: "tool-1", approved: true, remember: false },
      { "X-API-Key": "test-key" }
    );

    const response = await POST(request);
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      "http://backend/api/v1/tool-approval",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "X-API-Key": "test-key" }),
      })
    );
    expect(data).toEqual({ success: true });
  });
});

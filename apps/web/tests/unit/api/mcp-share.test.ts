/**
 * MCP share route tests
 */

import type { NextRequest } from "next/server";

const mockFetch = jest.fn();

global.fetch = mockFetch as typeof fetch;

function buildShareRequest(name: string, headers?: Record<string, string>) {
  const url = `http://localhost/api/mcp-servers/${name}/share`;
  return {
    headers: new Headers({
      "Content-Type": "application/json",
      ...(headers ?? {}),
    }),
    cookies: {
      get: () => undefined,
    },
    nextUrl: new URL(url),
    json: async () => ({}),
  } as unknown as NextRequest;
}

describe("MCP share flow", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = "http://backend/api/v1";
    jest.resetModules();
  });

  it("returns a share URL and resolves the token", async () => {
    const { POST } = await import("@/app/api/mcp-servers/[name]/share/route");
    const { GET } = await import("@/app/api/mcp-servers/share/[token]/route");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        server: {
          name: "postgres",
          type: "sse",
          url: "https://example.com",
          headers: { Authorization: "Bearer secret" },
          env: { API_KEY: "secret", LOG_LEVEL: "debug" },
        },
      }),
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        share_token: "token-123",
        config: {
          name: "postgres",
          type: "sse",
          url: "https://example.com",
          headers: { Authorization: "***REDACTED***" },
          env: { API_KEY: "***REDACTED***", LOG_LEVEL: "debug" },
        },
      }),
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        name: "postgres",
        config: {
          headers: { Authorization: "***REDACTED***" },
          env: { API_KEY: "***REDACTED***", LOG_LEVEL: "debug" },
        },
      }),
    });

    const shareResponse = await POST(
      buildShareRequest("postgres", { "X-API-Key": "test-key" }) as NextRequest,
      { params: { name: "postgres" } }
    );
    const shareData = await shareResponse.json();

    expect(shareData.share_url).toContain("/api/mcp-servers/share/");
    expect(shareData.share_token).toBe("token-123");

    const [_, shareCall] = mockFetch.mock.calls;
    const shareBody = JSON.parse(shareCall[1].body as string);
    expect(shareBody.config.env.API_KEY).toBe("***REDACTED***");
    expect(shareBody.config.headers.Authorization).toBe("***REDACTED***");

    const token = shareData.share_token as string;

    const getResponse = await GET(
      buildShareRequest("postgres", { "X-API-Key": "test-key" }) as NextRequest,
      { params: { token } }
    );
    const getData = await getResponse.json();

    expect(getData.config.env.API_KEY).toBe("***REDACTED***");
    expect(getData.config.headers.Authorization).toBe("***REDACTED***");
    expect(getData.config.env.LOG_LEVEL).toBe("debug");
  });

  it("returns 404 for invalid token", async () => {
    const { GET } = await import("@/app/api/mcp-servers/share/[token]/route");

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({
        error: { code: "MCP_SHARE_NOT_FOUND", message: "Share token not found" },
      }),
    });

    const response = await GET(
      buildShareRequest("postgres", { "X-API-Key": "test-key" }) as NextRequest,
      { params: { token: "bad" } }
    );

    expect(response.status).toBe(404);
  });
});

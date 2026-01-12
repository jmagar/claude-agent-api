/**
 * MCP servers BFF route tests
 */

import type { NextRequest } from 'next/server';

const mockFetch = jest.fn();

global.fetch = mockFetch as typeof fetch;

function buildRequest(headers?: Record<string, string>, body?: Record<string, unknown>) {
  return {
    headers: new Headers(headers ?? {}),
    cookies: {
      get: () => undefined,
    },
    json: async () => body ?? {},
  } as unknown as NextRequest;
}

describe('MCP servers BFF routes', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  const serverName = 'postgres';
  const serverConfig = {
    id: '00000000-0000-0000-0000-000000000003',
    name: serverName,
    transport_type: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres'],
    enabled: true,
    created_at: '2026-01-11T00:00:00Z',
    updated_at: '2026-01-11T00:00:00Z',
  };

  it('GET /api/mcp-servers returns servers wrapper', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ servers: [serverConfig] }),
    });

    const { GET } = await import('@/app/api/mcp-servers/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }));
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/mcp-servers',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data).toEqual({ servers: [serverConfig] });
  });

  it('POST /api/mcp-servers returns server details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ server: serverConfig }),
    });

    const { POST } = await import('@/app/api/mcp-servers/route');
    const response = await POST(
      buildRequest({ 'X-API-Key': 'test-key' }, { name: serverName, type: 'stdio' })
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/mcp-servers',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(serverConfig.id);
  });

  it('GET /api/mcp-servers/[name] returns server details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ server: serverConfig }),
    });

    const { GET } = await import('@/app/api/mcp-servers/[name]/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { name: serverName },
    });
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/mcp-servers/${serverName}`,
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(serverConfig.id);
  });

  it('GET /api/mcp-servers/[name]/resources returns resources wrapper', async () => {
    const resources = [
      { uri: 'file:///workspace/readme.md', name: 'readme', description: 'Readme' },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ resources }),
    });

    const { GET } = await import('@/app/api/mcp-servers/[name]/resources/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { name: serverName },
    });
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/mcp-servers/${serverName}/resources`,
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data).toEqual({ resources });
  });
});

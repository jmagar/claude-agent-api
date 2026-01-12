/**
 * Slash commands BFF route tests
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

describe('Slash commands BFF routes', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  it('GET /api/slash-commands returns 401 when API key is missing', async () => {
    const { GET } = await import('@/app/api/slash-commands/route');

    const response = await GET(buildRequest());

    expect(response.status).toBe(401);
  });

  it('GET /api/slash-commands proxies to backend with API key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ commands: [] }),
    });

    const { GET } = await import('@/app/api/slash-commands/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }));

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/slash-commands',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
  });

  it('POST /api/slash-commands proxies to backend with API key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ command: { id: 'cmd-1' } }),
    });

    const { POST } = await import('@/app/api/slash-commands/route');
    const response = await POST(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        {
          name: '/hello',
          description: 'Say hello',
          content: 'Hello!',
          enabled: true,
        }
      )
    );

    expect(response.status).toBe(201);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/slash-commands',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
  });

  it('GET /api/slash-commands/[id] proxies to backend with API key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ command: { id: 'cmd-1' } }),
    });

    const { GET } = await import('@/app/api/slash-commands/[id]/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: 'cmd-1' },
    });

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/slash-commands/cmd-1',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
  });

  it('PUT /api/slash-commands/[id] proxies to backend with API key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ command: { id: 'cmd-1' } }),
    });

    const { PUT } = await import('@/app/api/slash-commands/[id]/route');
    const response = await PUT(
      buildRequest({ 'X-API-Key': 'test-key' }, { enabled: false }),
      { params: { id: 'cmd-1' } }
    );

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/slash-commands/cmd-1',
      expect.objectContaining({
        method: 'PUT',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
  });

  it('DELETE /api/slash-commands/[id] proxies to backend with API key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { DELETE } = await import('@/app/api/slash-commands/[id]/route');
    const response = await DELETE(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: 'cmd-1' },
    });

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/slash-commands/cmd-1',
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
  });
});

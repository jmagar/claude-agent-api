/**
 * Tool presets API route tests
 */

import type { NextRequest } from 'next/server';

const mockFetch = jest.fn();

global.fetch = mockFetch as typeof fetch;

function buildRequest(
  body?: Record<string, unknown>,
  headers?: Record<string, string>
) {
  return {
    headers: new Headers({
      'Content-Type': 'application/json',
      ...(headers ?? {}),
    }),
    cookies: {
      get: () => undefined,
    },
    json: async () => body ?? {},
  } as unknown as NextRequest;
}

describe('Tool presets routes', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  it('GET /api/tool-presets returns 401 without API key', async () => {
    const { GET } = await import('@/app/api/tool-presets/route');
    const response = await GET(buildRequest());

    expect(response.status).toBe(401);
  });

  it('GET /api/tool-presets proxies to backend', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        presets: [
          { id: '1', name: 'Preset', allowed_tools: [], disallowed_tools: [] },
        ],
      }),
    });

    const { GET } = await import('@/app/api/tool-presets/route');
    const response = await GET(buildRequest({}, { 'X-API-Key': 'test-key' }));
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/tool-presets',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.presets).toHaveLength(1);
  });

  it('POST /api/tool-presets validates required fields', async () => {
    const { POST } = await import('@/app/api/tool-presets/route');
    const response = await POST(
      buildRequest({ name: 'Preset' }, { 'X-API-Key': 'test-key' })
    );

    expect(response.status).toBe(400);
  });

  it('POST /api/tool-presets proxies to backend', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '1', name: 'Preset', allowed_tools: [] }),
    });

    const { POST } = await import('@/app/api/tool-presets/route');
    const response = await POST(
      buildRequest(
        { name: 'Preset', tools: ['Read'] },
        { 'X-API-Key': 'test-key' }
      )
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/tool-presets',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.preset.id).toBe('1');
  });

  it('GET /api/tool-presets/{id} proxies to backend', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '1', name: 'Preset', allowed_tools: [] }),
    });

    const { GET } = await import('@/app/api/tool-presets/[id]/route');
    const response = await GET(
      buildRequest({}, { 'X-API-Key': 'test-key' }),
      { params: { id: '1' } }
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/tool-presets/1',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.preset.id).toBe('1');
  });

  it('PUT /api/tool-presets/{id} proxies to backend', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '1', name: 'Updated', allowed_tools: [] }),
    });

    const { PUT } = await import('@/app/api/tool-presets/[id]/route');
    const response = await PUT(
      buildRequest(
        { name: 'Updated', tools: [] },
        { 'X-API-Key': 'test-key' }
      ),
      { params: { id: '1' } }
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/tool-presets/1',
      expect.objectContaining({
        method: 'PUT',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.preset.name).toBe('Updated');
  });

  it('DELETE /api/tool-presets/{id} proxies to backend', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { DELETE } = await import('@/app/api/tool-presets/[id]/route');
    const response = await DELETE(
      buildRequest({}, { 'X-API-Key': 'test-key' }),
      { params: { id: '1' } }
    );

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/tool-presets/1',
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(response.status).toBe(200);
  });
});

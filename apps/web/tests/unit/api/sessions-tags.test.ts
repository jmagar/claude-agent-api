/**
 * Sessions tags BFF route tests
 */

import type { NextRequest } from 'next/server';

const mockFetch = jest.fn();

global.fetch = mockFetch as typeof fetch;

function buildRequest(body: Record<string, unknown>, headers?: Record<string, string>) {
  return {
    headers: new Headers({ 'Content-Type': 'application/json', ...(headers ?? {}) }),
    cookies: {
      get: () => undefined,
    },
    json: async () => body,
  } as unknown as NextRequest;
}

describe('PATCH /api/sessions/[id]/tags', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  it('returns 400 when tags is not an array', async () => {
    const { PATCH } = await import('@/app/api/sessions/[id]/tags/route');
    const response = await PATCH(buildRequest({ tags: 'oops' }), {
      params: { id: 'session-1' },
    });

    expect(response.status).toBe(400);
  });

  it('returns 401 when API key is missing', async () => {
    const { PATCH } = await import('@/app/api/sessions/[id]/tags/route');
    const response = await PATCH(buildRequest({ tags: ['one'] }), {
      params: { id: 'session-1' },
    });

    expect(response.status).toBe(401);
  });

  it('proxies tag update to backend with API key', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session: { id: 'session-1', tags: ['one'] } }),
    });

    const { PATCH } = await import('@/app/api/sessions/[id]/tags/route');
    const response = await PATCH(
      buildRequest({ tags: ['one'] }, { 'X-API-Key': 'test-key' }),
      { params: { id: 'session-1' } }
    );

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/sessions/session-1/tags',
      expect.objectContaining({
        method: 'PATCH',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
  });
});

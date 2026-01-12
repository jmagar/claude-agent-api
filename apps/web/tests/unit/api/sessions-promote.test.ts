/**
 * Sessions promote API route tests
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
    json: async () => body ?? {},
  } as unknown as NextRequest;
}

describe('POST /api/sessions/{id}/promote', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  it('returns 400 when project_id is missing', async () => {
    const { POST } = await import('@/app/api/sessions/[id]/promote/route');
    const response = await POST(buildRequest({}), { params: { id: 'session-1' } });

    expect(response.status).toBe(400);
  });

  it('proxies promotion to backend', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ session: { id: 'session-1' } }),
    });

    const { POST } = await import('@/app/api/sessions/[id]/promote/route');
    const response = await POST(
      buildRequest(
        { project_id: 'project-1' },
        { Authorization: 'Bearer token' }
      ),
      { params: { id: 'session-1' } }
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/sessions/session-1/promote',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer token' }),
      })
    );
    expect(data.session.id).toBe('session-1');
  });
});

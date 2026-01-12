/**
 * Projects BFF route tests
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
    url: 'http://localhost/api/projects',
  } as unknown as NextRequest;
}

describe('Projects BFF routes', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  const projectId = '00000000-0000-0000-0000-000000000006';

  it('GET /api/projects returns projects wrapper', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: [{ id: projectId, name: 'Project' }], total: 1 }),
    });

    const { GET } = await import('@/app/api/projects/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }));
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/projects',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.projects).toHaveLength(1);
    expect(data.total).toBe(1);
  });

  it('POST /api/projects returns project details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        project: {
          id: projectId,
          name: 'Project',
          path: 'project',
          created_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { POST } = await import('@/app/api/projects/route');
    const response = await POST(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        { name: 'Project', path: 'project' }
      )
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/projects',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(projectId);
  });

  it('GET /api/projects/[id] returns project details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        project: {
          id: projectId,
          name: 'Project',
          path: 'project',
          created_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { GET } = await import('@/app/api/projects/[id]/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: projectId },
    });
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/projects/${projectId}`,
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(projectId);
  });

  it('PATCH /api/projects/[id] returns project details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        project: {
          id: projectId,
          name: 'Project',
          path: 'project',
          created_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { PATCH } = await import('@/app/api/projects/[id]/route');
    const response = await PATCH(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        { name: 'Project', metadata: { owner: 'test' } }
      ),
      { params: { id: projectId } }
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/projects/${projectId}`,
      expect.objectContaining({
        method: 'PATCH',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(projectId);
  });

  it('DELETE /api/projects/[id] returns 204', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { DELETE } = await import('@/app/api/projects/[id]/route');
    const response = await DELETE(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: projectId },
    });

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/projects/${projectId}`,
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(response.status).toBe(204);
  });
});

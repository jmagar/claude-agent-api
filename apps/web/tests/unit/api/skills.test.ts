/**
 * Skills BFF route tests
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

describe('Skills BFF routes', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  const skillId = '00000000-0000-0000-0000-000000000005';

  it('GET /api/skills returns skills wrapper', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ skills: [{ id: skillId }] }),
    });

    const { GET } = await import('@/app/api/skills/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }));
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/skills',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.skills).toHaveLength(1);
  });

  it('POST /api/skills returns skill details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        skill: {
          id: skillId,
          name: 'Skill',
          description: 'Test skill',
          content: 'Do the thing',
          created_at: '2026-01-11T00:00:00Z',
          updated_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { POST } = await import('@/app/api/skills/route');
    const response = await POST(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        { name: 'Skill', description: 'Test skill', content: 'Do the thing' }
      )
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/skills',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(skillId);
  });

  it('GET /api/skills/[id] returns skill details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        skill: {
          id: skillId,
          name: 'Skill',
          description: 'Test skill',
          content: 'Do the thing',
          created_at: '2026-01-11T00:00:00Z',
          updated_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { GET } = await import('@/app/api/skills/[id]/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: skillId },
    });
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/skills/${skillId}`,
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(skillId);
  });

  it('PUT /api/skills/[id] returns skill details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        skill: {
          id: skillId,
          name: 'Skill',
          description: 'Test skill',
          content: 'Do the thing',
          created_at: '2026-01-11T00:00:00Z',
          updated_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { PUT } = await import('@/app/api/skills/[id]/route');
    const response = await PUT(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        { name: 'Skill', description: 'Test skill', content: 'Do the thing' }
      ),
      { params: { id: skillId } }
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/skills/${skillId}`,
      expect.objectContaining({
        method: 'PUT',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(skillId);
  });

  it('DELETE /api/skills/[id] returns 204', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { DELETE } = await import('@/app/api/skills/[id]/route');
    const response = await DELETE(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: skillId },
    });

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/skills/${skillId}`,
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(response.status).toBe(204);
  });
});

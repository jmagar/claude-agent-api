/**
 * Agents BFF route tests
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

describe('Agents BFF routes', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    process.env.API_BASE_URL = 'http://backend/api/v1';
    jest.resetModules();
  });

  const agentId = '00000000-0000-0000-0000-000000000004';

  it('GET /api/agents returns agents wrapper', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ agents: [{ id: agentId }] }),
    });

    const { GET } = await import('@/app/api/agents/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }));
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/agents',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.agents).toHaveLength(1);
  });

  it('POST /api/agents returns agent details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        agent: {
          id: agentId,
          name: 'Agent',
          description: 'Test agent',
          prompt: 'Be helpful',
          created_at: '2026-01-11T00:00:00Z',
          updated_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { POST } = await import('@/app/api/agents/route');
    const response = await POST(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        { name: 'Agent', description: 'Test agent', prompt: 'Be helpful' }
      )
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      'http://backend/api/v1/agents',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(agentId);
  });

  it('GET /api/agents/[id] returns agent details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        agent: {
          id: agentId,
          name: 'Agent',
          description: 'Test agent',
          prompt: 'Be helpful',
          created_at: '2026-01-11T00:00:00Z',
          updated_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { GET } = await import('@/app/api/agents/[id]/route');
    const response = await GET(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: agentId },
    });
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/agents/${agentId}`,
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(agentId);
  });

  it('PUT /api/agents/[id] returns agent details', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        agent: {
          id: agentId,
          name: 'Agent',
          description: 'Test agent',
          prompt: 'Be helpful',
          created_at: '2026-01-11T00:00:00Z',
          updated_at: '2026-01-11T00:00:00Z',
        },
      }),
    });

    const { PUT } = await import('@/app/api/agents/[id]/route');
    const response = await PUT(
      buildRequest(
        { 'X-API-Key': 'test-key' },
        { name: 'Agent', description: 'Test agent', prompt: 'Be helpful' }
      ),
      { params: { id: agentId } }
    );
    const data = await response.json();

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/agents/${agentId}`,
      expect.objectContaining({
        method: 'PUT',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(data.id).toBe(agentId);
  });

  it('DELETE /api/agents/[id] returns 204', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { DELETE } = await import('@/app/api/agents/[id]/route');
    const response = await DELETE(buildRequest({ 'X-API-Key': 'test-key' }), {
      params: { id: agentId },
    });

    expect(mockFetch).toHaveBeenCalledWith(
      `http://backend/api/v1/agents/${agentId}`,
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({ 'X-API-Key': 'test-key' }),
      })
    );
    expect(response.status).toBe(204);
  });
});

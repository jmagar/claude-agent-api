/**
 * MCP Server CRUD API Route
 *
 * BFF route for individual MCP server operations.
 * Proxies requests to Claude Agent API backend.
 *
 * Endpoints:
 * - GET /api/mcp-servers/[name] - Get server details
 * - PUT /api/mcp-servers/[name] - Update server configuration
 * - DELETE /api/mcp-servers/[name] - Delete server
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
}

function normalizeServer(server: Record<string, unknown>) {
  if (server.transport_type || !server.type) {
    return server;
  }
  return { ...server, transport_type: server.type };
}

interface RouteParams {
  params: {
    name: string;
  };
}

/**
 * GET /api/mcp-servers/[name]
 * Get detailed information about a specific MCP server
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { name } = params;
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Forward request to backend
    const backendUrl = `${BACKEND_API_URL}/mcp-servers/${encodeURIComponent(name)}`;
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Backend request failed' },
      }));

      return jsonResponse(
        {
          error: {
            code: error.error?.code ?? (response.status === 404 ? 'NOT_FOUND' : 'BACKEND_ERROR'),
            message: error.error?.message ?? 'Failed to fetch MCP server',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const server = data?.server ?? data;
    return jsonResponse(normalizeServer(server as Record<string, unknown>));
  } catch (error) {
    console.error(`MCP server GET error (${params.name}):`, error);
    return jsonResponse(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: error instanceof Error ? error.message : 'Internal server error',
        },
      },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/mcp-servers/[name]
 * Update an existing MCP server configuration
 */
export async function PUT(request: NextRequest, { params }: RouteParams) {
  try {
    const { name } = params;
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Parse request body
    const body = await request.json();

    // Map transport_type to type for backend compatibility
    const backendRequest = {
      ...body,
      type: body.transport_type || body.type,
    };

    // Forward request to backend
    const backendUrl = `${BACKEND_API_URL}/mcp-servers/${encodeURIComponent(name)}`;
    const response = await fetch(backendUrl, {
      method: 'PUT',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendRequest),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Backend request failed' },
      }));

      return jsonResponse(
        {
          error: {
            code: error.error?.code ?? (response.status === 404 ? 'NOT_FOUND' : 'BACKEND_ERROR'),
            message: error.error?.message ?? 'Failed to update MCP server',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const server = data?.server ?? data;
    return jsonResponse(normalizeServer(server as Record<string, unknown>));
  } catch (error) {
    console.error(`MCP server PUT error (${params.name}):`, error);
    return jsonResponse(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: error instanceof Error ? error.message : 'Internal server error',
        },
      },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/mcp-servers/[name]
 * Delete an MCP server configuration
 */
export async function DELETE(request: NextRequest, { params }: RouteParams) {
  try {
    const { name } = params;
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Forward request to backend
    const backendUrl = `${BACKEND_API_URL}/mcp-servers/${encodeURIComponent(name)}`;
    const response = await fetch(backendUrl, {
      method: 'DELETE',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Backend request failed' },
      }));

      return jsonResponse(
        {
          error: {
            code: error.error?.code ?? (response.status === 404 ? 'NOT_FOUND' : 'BACKEND_ERROR'),
            message: error.error?.message ?? 'Failed to delete MCP server',
          },
        },
        { status: response.status }
      );
    }

    // Return 204 No Content on successful deletion
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error(`MCP server DELETE error (${params.name}):`, error);
    return jsonResponse(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: error instanceof Error ? error.message : 'Internal server error',
        },
      },
      { status: 500 }
    );
  }
}

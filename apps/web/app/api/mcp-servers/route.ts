/**
 * MCP Servers API Route
 *
 * BFF (Backend For Frontend) route for MCP server management.
 * Proxies requests to Claude Agent API backend.
 *
 * Endpoints:
 * - GET /api/mcp-servers - List all MCP servers
 * - POST /api/mcp-servers - Create new MCP server
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

/**
 * GET /api/mcp-servers
 * List all configured MCP servers
 */
export async function GET(request: NextRequest) {
  try {
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return NextResponse.json(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Forward request to backend
    const backendUrl = `${BACKEND_API_URL}/mcp-servers`;
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

      return NextResponse.json(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to fetch MCP servers',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const servers = Array.isArray(data)
      ? data
      : Array.isArray(data.servers)
        ? data.servers
        : [];
    return jsonResponse({
      servers: servers.map((server) =>
        normalizeServer(server as Record<string, unknown>)
      ),
    });
  } catch (error) {
    console.error('MCP servers GET error:', error);
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
 * POST /api/mcp-servers
 * Create a new MCP server configuration
 */
export async function POST(request: NextRequest) {
  try {
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return NextResponse.json(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Parse and validate request body
    const body = await request.json();

    // Map transport_type to type for backend compatibility
    const backendRequest = {
      ...body,
      type: body.transport_type || body.type,
    };

    // Basic validation
    if (!backendRequest.name || !backendRequest.type) {
      return jsonResponse(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Server name and transport_type/type are required',
          },
        },
        { status: 400 }
      );
    }

    // Forward request to backend
    const backendUrl = `${BACKEND_API_URL}/mcp-servers`;
    const response = await fetch(backendUrl, {
      method: 'POST',
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

      return NextResponse.json(
        {
          error: {
            code: error.error?.code ?? 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to create MCP server',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const server = data?.server ?? data;
    return jsonResponse(normalizeServer(server as Record<string, unknown>), {
      status: 201,
    });
  } catch (error) {
    console.error('MCP servers POST error:', error);
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

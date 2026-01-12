/**
 * MCP Server Resources API Route
 *
 * BFF route for listing MCP server resources.
 * Proxies requests to Claude Agent API backend.
 *
 * Endpoints:
 * - GET /api/mcp-servers/[name]/resources - List server resources
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

interface RouteParams {
  params: {
    name: string;
  };
}

/**
 * GET /api/mcp-servers/[name]/resources
 * List all resources provided by a specific MCP server
 */
export async function GET(request: NextRequest, { params }: RouteParams) {
  try {
    const { name } = params;
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return NextResponse.json(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Forward request to backend
    const backendUrl = `${BACKEND_API_URL}/mcp-servers/${encodeURIComponent(name)}/resources`;
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
            code: error.error?.code ?? 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to fetch MCP server resources',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(`MCP server resources GET error (${params.name}):`, error);
    return NextResponse.json(
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

/**
 * MCP Server Share API Route
 *
 * BFF route for generating shareable MCP server configurations.
 * Sanitizes credentials before sharing.
 *
 * Endpoints:
 * - POST /api/mcp-servers/[name]/share - Generate share link
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:54000/api/v1';

interface RouteParams {
  params: {
    name: string;
  };
}

/**
 * Sanitize MCP server config for sharing
 * Removes sensitive information like credentials, API keys, etc.
 */
function sanitizeConfig(config: Record<string, unknown>): Record<string, unknown> {
  const sanitized = { ...config };

  // Remove or redact sensitive fields
  if (sanitized.env && typeof sanitized.env === 'object') {
    const env = sanitized.env as Record<string, string>;
    const sanitizedEnv: Record<string, string> = {};

    // Redact values for known sensitive keys
    const sensitiveKeys = [
      'api_key',
      'apikey',
      'secret',
      'password',
      'token',
      'auth',
      'credential',
      'private',
    ];

    for (const [key, value] of Object.entries(env)) {
      const lowerKey = key.toLowerCase();
      const isSensitive = sensitiveKeys.some((pattern) => lowerKey.includes(pattern));

      if (isSensitive) {
        sanitizedEnv[key] = '***REDACTED***';
      } else {
        sanitizedEnv[key] = value;
      }
    }

    sanitized.env = sanitizedEnv;
  }

  // Remove headers that might contain auth
  if (sanitized.headers && typeof sanitized.headers === 'object') {
    const headers = sanitized.headers as Record<string, string>;
    const sanitizedHeaders: Record<string, string> = {};

    for (const [key, value] of Object.entries(headers)) {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('auth') || lowerKey.includes('token')) {
        sanitizedHeaders[key] = '***REDACTED***';
      } else {
        sanitizedHeaders[key] = value;
      }
    }

    sanitized.headers = sanitizedHeaders;
  }

  return sanitized;
}

/**
 * POST /api/mcp-servers/[name]/share
 * Generate a shareable link for an MCP server configuration
 */
export async function POST(request: NextRequest, { params }: RouteParams) {
  try {
    const { name } = params;
    const apiKey = request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;

    if (!apiKey) {
      return NextResponse.json(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // First, fetch the server configuration
    const getBackendUrl = `${BACKEND_API_URL}/mcp-servers/${encodeURIComponent(name)}`;
    const getResponse = await fetch(getBackendUrl, {
      method: 'GET',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
    });

    if (!getResponse.ok) {
      const error = await getResponse.json().catch(() => ({
        error: { message: 'Failed to fetch server config' },
      }));

      return NextResponse.json(
        {
          error: {
            code: error.error?.code ?? 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to fetch MCP server for sharing',
          },
        },
        { status: getResponse.status }
      );
    }

    const serverData = await getResponse.json();
    const serverConfig = serverData.server;

    // Sanitize the configuration
    const sanitizedConfig = sanitizeConfig(serverConfig);

    // Generate share token (simple approach - use timestamp + random string)
    const shareToken = `${Date.now()}-${Math.random().toString(36).substring(7)}`;
    const shareUrl = `${request.nextUrl.origin}/share/mcp/${shareToken}`;

    // TODO: Store sanitized config with share token in database for later retrieval
    // For now, just return the share URL and sanitized config

    return NextResponse.json({
      share_url: shareUrl,
      share_token: shareToken,
      config: sanitizedConfig,
    });
  } catch (error) {
    console.error(`MCP server share error (${params.name}):`, error);
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

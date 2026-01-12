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

const BACKEND_API_URL =
  process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

interface RouteParams {
  params: {
    name: string;
  };
}

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
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
    const apiKey =
      request.headers.get('X-API-Key') || request.cookies?.get('api-key')?.value;

    if (!apiKey) {
      return jsonResponse(
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

      return jsonResponse(
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

    const shareResponse = await fetch(
      `${BACKEND_API_URL}/mcp-servers/${encodeURIComponent(name)}/share`,
      {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config: sanitizedConfig }),
      }
    );

    if (!shareResponse.ok) {
      const error = await shareResponse.json().catch(() => ({
        error: { message: 'Failed to create share token' },
      }));

      return jsonResponse(
        {
          error: {
            code: error.error?.code ?? 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to create share token',
          },
        },
        { status: shareResponse.status }
      );
    }

    const shareData = await shareResponse.json();
    const shareToken = shareData.share_token;
    const shareUrl = `${request.nextUrl.origin}/api/mcp-servers/share/${shareToken}`;

    return jsonResponse({
      share_url: shareUrl,
      share_token: shareToken,
      config: shareData.config ?? sanitizedConfig,
    });
  } catch (error) {
    console.error(`MCP server share error (${params.name}):`, error);
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

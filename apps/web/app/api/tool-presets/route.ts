/**
 * Tool Presets API Route
 *
 * BFF endpoint for tool preset management.
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
}

function getApiKey(request: NextRequest) {
  return request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;
}

function mapPreset(preset: Record<string, unknown>) {
  const allowed_tools = Array.isArray(preset.allowed_tools)
    ? preset.allowed_tools
    : Array.isArray(preset.tools)
      ? preset.tools
      : [];
  return {
    id: preset.id,
    name: preset.name,
    description: preset.description,
    allowed_tools,
    disallowed_tools: preset.disallowed_tools || [],
    created_at: preset.created_at,
    is_system: !!(preset.is_system ?? preset.is_default),
  };
}

export async function GET(request: NextRequest) {
  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/tool-presets`, {
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
            code: 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to fetch tool presets',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const presets = Array.isArray(data.presets)
      ? data.presets.map(mapPreset)
      : [];
    return jsonResponse({ presets });
  } catch (error) {
    console.error('Tool presets GET error:', error);
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

export async function POST(request: NextRequest) {
  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const body = await request.json();
    if (!body?.name || typeof body.name !== 'string') {
      return jsonResponse(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Preset name is required',
          },
        },
        { status: 400 }
      );
    }

    if (!Array.isArray(body.tools)) {
      return jsonResponse(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Preset tools must be an array',
          },
        },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/tool-presets`, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: body.name,
        description: body.description,
        allowed_tools: body.tools,
        disallowed_tools: Array.isArray(body.disallowed_tools)
          ? body.disallowed_tools
          : [],
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Backend request failed' },
      }));
      return jsonResponse(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to create tool preset',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const preset = data && typeof data === 'object' ? mapPreset(data) : data;
    return jsonResponse(preset as Record<string, unknown>, { status: 201 });
  } catch (error) {
    console.error('Tool presets POST error:', error);
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

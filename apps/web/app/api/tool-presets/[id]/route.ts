/**
 * Tool Preset CRUD API Route
 *
 * BFF endpoint for individual tool preset operations:
 * - GET: Fetch single tool preset by ID
 * - PUT: Update existing tool preset
 * - DELETE: Delete tool preset
 *
 * Proxies requests to the backend Claude Agent API.
 */

import { NextRequest, NextResponse } from 'next/server';
import { isUUID } from '@/lib/validation/uuid';

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

function mapPreset(preset: Record<string, any>) {
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

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  if (!isUUID(params.id)) {
    return NextResponse.json(
      {
        error: {
          code: 'INVALID_ID',
          message: 'Invalid tool preset ID format (UUID expected)',
        },
      },
      { status: 400 }
    );
  }

  try {
    const { id } = params;
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/tool-presets/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to fetch tool preset' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to fetch tool preset' },
        { status: response.status }
      );
    }

    const data = await response.json();
    const preset = data && typeof data === 'object' ? mapPreset(data) : data;
    return jsonResponse(preset as any);
  } catch (error) {
    console.error('Error fetching tool preset:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  if (!isUUID(params.id)) {
    return NextResponse.json(
      {
        error: {
          code: 'INVALID_ID',
          message: 'Invalid tool preset ID format (UUID expected)',
        },
      },
      { status: 400 }
    );
  }

  try {
    const { id } = params;
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }
    const body = await request.json();

    const response = await fetch(`${API_BASE_URL}/tool-presets/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        name: body.name,
        description: body.description,
        allowed_tools: body.allowed_tools || body.tools,
        disallowed_tools: body.disallowed_tools || [],
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to update tool preset' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to update tool preset' },
        { status: response.status }
      );
    }

    const data = await response.json();
    const preset = data && typeof data === 'object' ? mapPreset(data) : data;
    return jsonResponse(preset as any);
  } catch (error) {
    console.error('Error updating tool preset:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  if (!isUUID(params.id)) {
    return NextResponse.json(
      {
        error: {
          code: 'INVALID_ID',
          message: 'Invalid tool preset ID format (UUID expected)',
        },
      },
      { status: 400 }
    );
  }

  try {
    const { id } = params;
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/tool-presets/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to delete tool preset' },
      }));
      return jsonResponse(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to delete tool preset',
          },
        },
        { status: response.status }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting tool preset:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

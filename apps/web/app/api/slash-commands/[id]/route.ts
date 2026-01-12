/**
 * Slash Command CRUD API Route
 *
 * BFF endpoint for individual slash command operations:
 * - GET: Fetch single slash command by ID
 * - PUT: Update existing slash command
 * - DELETE: Delete slash command
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

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  if (!isUUID(params.id)) {
    return NextResponse.json(
      {
        error: {
          code: 'INVALID_ID',
          message: 'Invalid slash command ID format (UUID expected)',
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

    const response = await fetch(`${API_BASE_URL}/slash-commands/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to fetch slash command' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to fetch slash command' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse(data as any);
  } catch (error) {
    console.error('Error fetching slash command:', error);
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
          message: 'Invalid slash command ID format (UUID expected)',
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

    const response = await fetch(`${API_BASE_URL}/slash-commands/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to update slash command' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to update slash command' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse(data as any);
  } catch (error) {
    console.error('Error updating slash command:', error);
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
          message: 'Invalid slash command ID format (UUID expected)',
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

    const response = await fetch(`${API_BASE_URL}/slash-commands/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to delete slash command' },
      }));
      return jsonResponse(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to delete slash command',
          },
        },
        { status: response.status }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting slash command:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

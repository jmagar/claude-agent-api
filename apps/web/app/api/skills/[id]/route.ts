/**
 * Skill Detail API Route
 *
 * BFF endpoint for skill details.
 */

import { NextRequest, NextResponse } from 'next/server';
import { isUUID } from '@/lib/validation/uuid';
import type { SkillDefinition } from '@/types';

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
          message: 'Invalid skill ID format (UUID expected)',
        },
      },
      { status: 400 }
    );
  }

  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/skills/${params.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to fetch skill' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to fetch skill' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse(data as any);
  } catch (error) {
    console.error('Error fetching skill:', error);
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
          message: 'Invalid skill ID format (UUID expected)',
        },
      },
      { status: 400 }
    );
  }

  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const body = await request.json();

    if (!body.name || typeof body.name !== 'string') {
      return jsonResponse(
        { error: 'Name is required and must be a string' },
        { status: 400 }
      );
    }

    if (!body.description || typeof body.description !== 'string') {
      return jsonResponse(
        { error: 'Description is required and must be a string' },
        { status: 400 }
      );
    }

    if (!body.content || typeof body.content !== 'string') {
      return jsonResponse(
        { error: 'Content is required and must be a string' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/skills/${params.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        id: params.id,
        name: body.name,
        description: body.description,
        content: body.content,
        enabled: body.enabled ?? true,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to update skill' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to update skill' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse(data as any);
  } catch (error) {
    console.error('Error updating skill:', error);
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
          message: 'Invalid skill ID format (UUID expected)',
        },
      },
      { status: 400 }
    );
  }

  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/skills/${params.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to delete skill' },
      }));
      return jsonResponse(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.error?.message ?? 'Failed to delete skill',
          },
        },
        { status: response.status }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting skill:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

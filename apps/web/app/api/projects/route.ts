/**
 * Projects API Route
 *
 * BFF endpoint for project management.
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

export async function GET(request: NextRequest) {
  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const sort = searchParams.get('sort') || 'last_accessed_at';
    const order = searchParams.get('order') || 'desc';

    const response = await fetch(`${API_BASE_URL}/projects`, {
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
            message: error.error?.message ?? 'Failed to fetch projects',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    let projects = data.projects || [];

    // Apply sorting
    projects.sort((a: any, b: any) => {
      const valA = a[sort];
      const valB = b[sort];
      if (valA < valB) return order === 'asc' ? -1 : 1;
      if (valA > valB) return order === 'asc' ? 1 : -1;
      return 0;
    });

    return jsonResponse({
      projects,
      total: data.total ?? projects.length,
    });
  } catch (error) {
    console.error('Projects GET error:', error);
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
    if (!body?.name || typeof body.name !== 'string' || body.name.length < 1 || body.name.length > 100) {
      return jsonResponse(
        {
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Project name is required and must be between 1 and 100 characters',
          },
        },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: body.name,
        path: body.path,
        metadata: body.metadata,
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
            message: error.error?.message ?? 'Failed to create project',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    const project = data?.project ?? data;
    return jsonResponse(project as Record<string, unknown>, { status: 201 });
  } catch (error) {
    console.error('Projects POST error:', error);
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

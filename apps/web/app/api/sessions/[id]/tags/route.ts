/**
 * Session Tags API Route
 *
 * BFF endpoint for updating session tags:
 * - PATCH: Update session tags
 *
 * Proxies requests to the backend Claude Agent API.
 * Note: This is a convenience endpoint. Tags can also be updated via PATCH /api/sessions/[id]
 *
 * @example PATCH /api/sessions/session-123/tags { tags: ['bug', 'auth'] }
 */

import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

function getApiKey(request: NextRequest) {
  return request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;
}

/**
 * PATCH /api/sessions/[id]/tags
 *
 * Update session tags
 *
 * Request body:
 * {
 *   tags: string[]
 * }
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await request.json();
    const apiKey = getApiKey(request);

    // Validate tags field
    if (!Array.isArray(body.tags)) {
      return NextResponse.json(
        { error: 'Tags must be an array of strings' },
        { status: 400 }
      );
    }

    if (!apiKey) {
      return NextResponse.json(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    // Validate all tags are strings
    if (!body.tags.every((tag: unknown) => typeof tag === 'string')) {
      return NextResponse.json(
        { error: 'All tags must be strings' },
        { status: 400 }
      );
    }

    // Use the tags endpoint
    const response = await fetch(`${API_BASE_URL}/sessions/${id}/tags`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        tags: body.tags,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to update tags' }));
      return NextResponse.json(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.message || 'Failed to update tags',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error updating tags:', error);
    return NextResponse.json(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Internal server error',
        },
      },
      { status: 500 }
    );
  }
}

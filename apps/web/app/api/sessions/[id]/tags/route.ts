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
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:54000';

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

    // Validate tags field
    if (!Array.isArray(body.tags)) {
      return NextResponse.json(
        { error: 'Tags must be an array of strings' },
        { status: 400 }
      );
    }

    // Validate all tags are strings
    if (!body.tags.every((tag: unknown) => typeof tag === 'string')) {
      return NextResponse.json(
        { error: 'All tags must be strings' },
        { status: 400 }
      );
    }

    // Use the main session update endpoint
    const response = await fetch(`${API_BASE_URL}/sessions/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
      body: JSON.stringify({
        tags: body.tags,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to update tags' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      session: data.session as Session,
    });
  } catch (error) {
    console.error('Error updating tags:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * Session CRUD API Route
 *
 * BFF endpoints for individual session operations:
 * - GET: Fetch session details
 * - PATCH: Update session metadata
 * - DELETE: Delete a session
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example GET /api/sessions/session-123
 * @example PATCH /api/sessions/session-123 { title: 'Updated Title' }
 * @example DELETE /api/sessions/session-123
 */

import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:54000';

/**
 * GET /api/sessions/[id]
 *
 * Fetch session details by ID
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/sessions/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to fetch session' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      session: data.session as Session,
    });
  } catch (error) {
    console.error('Error fetching session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * PATCH /api/sessions/[id]
 *
 * Update session metadata
 *
 * Request body:
 * {
 *   title?: string,
 *   tags?: string[]
 * }
 */
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await request.json();

    // Validate at least one field is present
    if (!body.title && !body.tags) {
      return NextResponse.json(
        { error: 'At least one field (title or tags) must be provided' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/sessions/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
      body: JSON.stringify({
        title: body.title,
        tags: body.tags,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to update session' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      session: data.session as Session,
    });
  } catch (error) {
    console.error('Error updating session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/sessions/[id]
 *
 * Delete a session
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/sessions/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to delete session' },
        { status: response.status }
      );
    }

    return NextResponse.json(
      { success: true },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error deleting session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

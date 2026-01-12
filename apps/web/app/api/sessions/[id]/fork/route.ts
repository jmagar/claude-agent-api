/**
 * Session Fork API Route
 *
 * BFF endpoint for forking a session from a checkpoint:
 * - POST: Fork session from a specific checkpoint
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example POST /api/sessions/session-123/fork { checkpoint_index: 5 }
 */

import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

/**
 * POST /api/sessions/[id]/fork
 *
 * Fork a session from a checkpoint
 *
 * Request body:
 * {
 *   checkpoint_index: number,
 *   title?: string
 * }
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await request.json();

    // Validate required fields
    if (
      typeof body.checkpoint_index !== 'number' ||
      body.checkpoint_index < 0
    ) {
      return NextResponse.json(
        { error: 'Invalid or missing checkpoint_index (must be a non-negative number)' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/sessions/${id}/fork`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
      body: JSON.stringify({
        checkpoint_index: body.checkpoint_index,
        title: body.title,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to fork session' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      session: data.session as Session,
    }, { status: 201 });
  } catch (error) {
    console.error('Error forking session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

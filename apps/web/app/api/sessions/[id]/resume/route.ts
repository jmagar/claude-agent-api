/**
 * Session Resume API Route
 *
 * BFF endpoint for resuming a session:
 * - POST: Resume an existing session
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example POST /api/sessions/session-123/resume
 */

import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

/**
 * POST /api/sessions/[id]/resume
 *
 * Resume a session
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/sessions/${id}/resume`, {
      method: 'POST',
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
        { error: error.message || 'Failed to resume session' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      session: data.session as Session,
    });
  } catch (error) {
    console.error('Error resuming session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

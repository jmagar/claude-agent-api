/**
 * Sessions API Route
 *
 * BFF endpoint for session management:
 * - GET: Fetch all sessions
 * - POST: Create a new session
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example GET /api/sessions
 * @example POST /api/sessions { mode: 'brainstorm', title: 'New Session' }
 */

import { NextRequest, NextResponse } from 'next/server';
import type { Session, SessionMode } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

/**
 * GET /api/sessions
 *
 * Fetch all sessions for the current user
 */
export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Forward auth headers if present
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to fetch sessions' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      sessions: data.sessions || [],
    });
  } catch (error) {
    console.error('Error fetching sessions:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/sessions
 *
 * Create a new session
 *
 * Request body:
 * {
 *   mode: 'brainstorm' | 'code',
 *   title?: string,
 *   project_id?: string,
 *   tags?: string[]
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate required fields
    if (!body.mode || !['brainstorm', 'code'].includes(body.mode)) {
      return NextResponse.json(
        { error: 'Invalid or missing mode (must be "brainstorm" or "code")' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
      body: JSON.stringify({
        mode: body.mode as SessionMode,
        title: body.title,
        project_id: body.project_id,
        tags: body.tags,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to create session' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      session: data.session as Session,
    }, { status: 201 });
  } catch (error) {
    console.error('Error creating session:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

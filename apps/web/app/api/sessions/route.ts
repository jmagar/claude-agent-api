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
  process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

/**
 * GET /api/sessions
 *
 * Fetch all sessions for the current user
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const mode = searchParams.get('mode');
    const project_id = searchParams.get('project_id');
    const tags = searchParams.getAll('tags');
    const search = searchParams.get('search');
    const page = parseInt(searchParams.get('page') || '1');
    const page_size = parseInt(searchParams.get('page_size') || '50');

    const backendUrl = new URL(`${API_BASE_URL}/sessions`);
    if (mode) backendUrl.searchParams.set('mode', mode);
    if (project_id) backendUrl.searchParams.set('project_id', project_id);
    if (search) backendUrl.searchParams.set('search', search);
    backendUrl.searchParams.set('page', page.toString());
    backendUrl.searchParams.set('page_size', page_size.toString());
    tags.forEach(tag => backendUrl.searchParams.append('tags', tag));

    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Forward auth headers if present
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
        ...(request.headers.get('x-api-key')
          ? { 'X-API-Key': request.headers.get('x-api-key')! }
          : {}),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to fetch sessions' }));
      return NextResponse.json(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.message || 'Failed to fetch sessions',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      sessions: data.sessions || [],
      total: data.total ?? (data.sessions ? data.sessions.length : 0),
      page: data.page ?? page,
      page_size: data.page_size ?? page_size,
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
        ...(request.headers.get('x-api-key')
          ? { 'X-API-Key': request.headers.get('x-api-key')! }
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
      const error = await response.json().catch(() => ({ message: 'Failed to create session' }));
      return NextResponse.json(
        {
          error: {
            code: 'BACKEND_ERROR',
            message: error.message || 'Failed to create session',
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error('Error creating session:', error);
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

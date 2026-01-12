/**
 * Session Promote API Route
 *
 * BFF endpoint for promoting a brainstorm session to code mode.
 */

import { NextRequest, NextResponse } from 'next/server';
import type { Session } from '@/types';

const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
}

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    if (!body?.project_id || typeof body.project_id !== 'string') {
      return jsonResponse(
        { error: 'Project ID is required' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/sessions/${params.id}/promote`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
        ...(request.headers.get('X-API-Key') || request.cookies?.get('api-key')?.value
          ? {
              'X-API-Key':
                request.headers.get('X-API-Key') ||
                request.cookies?.get('api-key')?.value ||
                '',
            }
          : {}),
      },
      body: JSON.stringify({ project_id: body.project_id }),
    });

    if (!response.ok) {
      const error = await response.json();
      return jsonResponse(
        { error: error.message || 'Failed to promote session' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse({ session: data.session as Session });
  } catch (error) {
    console.error('Error promoting session:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

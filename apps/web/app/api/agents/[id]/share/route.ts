/**
 * Agent Share API Route
 *
 * BFF endpoint for generating shareable agent configurations:
 * - POST: Generate public share URL for an agent
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example POST /api/agents/agent-123/share
 */

import { NextRequest, NextResponse } from 'next/server';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

/**
 * POST /api/agents/[id]/share
 *
 * Generate a public share URL for an agent
 * Returns a URL that can be used to import the agent configuration
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/agents/${id}/share`, {
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
        { error: error.message || 'Failed to share agent' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      share_url: data.share_url,
      agent_id: id,
    });
  } catch (error) {
    console.error('Error sharing agent:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

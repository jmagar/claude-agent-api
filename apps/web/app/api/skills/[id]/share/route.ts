/**
 * Skill Share API Route
 *
 * BFF endpoint for generating shareable skill configurations:
 * - POST: Generate public share URL for a skill
 *
 * Proxies requests to the backend Claude Agent API.
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:54000';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/skills/${id}/share`, {
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
        { error: error.message || 'Failed to share skill' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ share_url: data.share_url, skill_id: id });
  } catch (error) {
    console.error('Error sharing skill:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

/**
 * Session Checkpoints API Route
 *
 * BFF endpoint for fetching session checkpoints:
 * - GET: Get all checkpoints for a session
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example GET /api/sessions/session-123/checkpoints
 */

import { NextRequest, NextResponse } from 'next/server';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:54000';

/**
 * Checkpoint interface
 */
export interface Checkpoint {
  /**
   * Message index where checkpoint occurs
   */
  message_index: number;

  /**
   * Timestamp when checkpoint was created
   */
  timestamp: string;

  /**
   * Optional title or description
   */
  title?: string;

  /**
   * Whether this checkpoint has been forked
   */
  is_forked?: boolean;
}

/**
 * GET /api/sessions/[id]/checkpoints
 *
 * Fetch all checkpoints for a session
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/sessions/${id}/checkpoints`, {
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
        { error: error.message || 'Failed to fetch checkpoints' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      checkpoints: (data.checkpoints || []) as Checkpoint[],
    });
  } catch (error) {
    console.error('Error fetching checkpoints:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

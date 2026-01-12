/**
 * Slash Command CRUD API Route
 *
 * BFF endpoint for individual slash command operations:
 * - GET: Fetch single slash command by ID
 * - PUT: Update existing slash command
 * - DELETE: Delete slash command
 *
 * Proxies requests to the backend Claude Agent API.
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SlashCommand } from '@/types';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:54000';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/slash-commands/${id}`, {
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
        { error: error.message || 'Failed to fetch slash command' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ command: data.command as SlashCommand });
  } catch (error) {
    console.error('Error fetching slash command:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await request.json();

    const response = await fetch(`${API_BASE_URL}/slash-commands/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to update slash command' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ command: data.command as SlashCommand });
  } catch (error) {
    console.error('Error updating slash command:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/slash-commands/${id}`, {
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
        { error: error.message || 'Failed to delete slash command' },
        { status: response.status }
      );
    }

    return NextResponse.json({ message: 'Slash command deleted successfully' }, { status: 200 });
  } catch (error) {
    console.error('Error deleting slash command:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

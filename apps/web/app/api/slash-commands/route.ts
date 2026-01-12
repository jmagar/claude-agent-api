/**
 * Slash Commands API Route
 *
 * BFF endpoint for slash command management:
 * - GET: Fetch all slash commands
 * - POST: Create a new slash command
 *
 * Proxies requests to the backend Claude Agent API.
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SlashCommand } from '@/types';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:54000';

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/slash-commands`, {
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
        { error: error.message || 'Failed to fetch slash commands' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ commands: data.commands || [] });
  } catch (error) {
    console.error('Error fetching slash commands:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    if (!body.name || typeof body.name !== 'string') {
      return NextResponse.json({ error: 'Name is required and must be a string' }, { status: 400 });
    }

    if (!body.description || typeof body.description !== 'string') {
      return NextResponse.json({ error: 'Description is required and must be a string' }, { status: 400 });
    }

    if (!body.content || typeof body.content !== 'string') {
      return NextResponse.json({ error: 'Content is required and must be a string' }, { status: 400 });
    }

    const response = await fetch(`${API_BASE_URL}/slash-commands`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
      body: JSON.stringify({
        name: body.name,
        description: body.description,
        content: body.content,
        enabled: body.enabled ?? true,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to create slash command' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ command: data.command as SlashCommand }, { status: 201 });
  } catch (error) {
    console.error('Error creating slash command:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

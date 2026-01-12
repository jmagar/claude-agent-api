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

const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000/api/v1';

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
}

function getApiKey(request: NextRequest) {
  return request.headers.get('X-API-Key') || request.cookies.get('api-key')?.value;
}

export async function GET(request: NextRequest) {
  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/slash-commands`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to fetch slash commands' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to fetch slash commands' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse({ commands: data.commands || [] });
  } catch (error) {
    console.error('Error fetching slash commands:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const apiKey = getApiKey(request);
    if (!apiKey) {
      return jsonResponse(
        { error: { code: 'INVALID_API_KEY', message: 'API key is required' } },
        { status: 401 }
      );
    }

    const body = await request.json();

    if (!body.name || typeof body.name !== 'string') {
      return jsonResponse(
        { error: 'Name is required and must be a string' },
        { status: 400 }
      );
    }

    if (!body.description || typeof body.description !== 'string') {
      return jsonResponse(
        { error: 'Description is required and must be a string' },
        { status: 400 }
      );
    }

    if (!body.content || typeof body.content !== 'string') {
      return jsonResponse(
        { error: 'Content is required and must be a string' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/slash-commands`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: JSON.stringify({
        name: body.name,
        description: body.description,
        content: body.content,
        enabled: body.enabled ?? true,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'Failed to create slash command' },
      }));
      return jsonResponse(
        { error: error.error?.message ?? 'Failed to create slash command' },
        { status: response.status }
      );
    }

    const data = await response.json();
    const command = data?.command ?? data;
    return jsonResponse(command as Record<string, unknown>, { status: 201 });
  } catch (error) {
    console.error('Error creating slash command:', error);
    return jsonResponse({ error: 'Internal server error' }, { status: 500 });
  }
}

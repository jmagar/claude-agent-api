/**
 * Skills API Route
 *
 * BFF endpoint for skill management:
 * - GET: Fetch all skills
 * - POST: Create a new skill
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example GET /api/skills
 * @example POST /api/skills { name: 'my-skill', description: '...', content: '...' }
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SkillDefinition } from '@/types';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:54000';

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/skills`, {
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
        { error: error.message || 'Failed to fetch skills' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ skills: data.skills || [] });
  } catch (error) {
    console.error('Error fetching skills:', error);
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

    const response = await fetch(`${API_BASE_URL}/skills`, {
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
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to create skill' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ skill: data.skill as SkillDefinition }, { status: 201 });
  } catch (error) {
    console.error('Error creating skill:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

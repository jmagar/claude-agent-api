/**
 * Skill CRUD API Route
 *
 * BFF endpoint for individual skill operations:
 * - GET: Fetch single skill by ID
 * - PUT: Update existing skill
 * - DELETE: Delete skill
 *
 * Proxies requests to the backend Claude Agent API.
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SkillDefinition } from '@/types';

const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:54000';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/skills/${id}`, {
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
        { error: error.message || 'Failed to fetch skill' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ skill: data.skill as SkillDefinition });
  } catch (error) {
    console.error('Error fetching skill:', error);
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

    const response = await fetch(`${API_BASE_URL}/skills/${id}`, {
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
        { error: error.message || 'Failed to update skill' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ skill: data.skill as SkillDefinition });
  } catch (error) {
    console.error('Error updating skill:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/skills/${id}`, {
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
        { error: error.message || 'Failed to delete skill' },
        { status: response.status }
      );
    }

    return NextResponse.json({ message: 'Skill deleted successfully' }, { status: 200 });
  } catch (error) {
    console.error('Error deleting skill:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}

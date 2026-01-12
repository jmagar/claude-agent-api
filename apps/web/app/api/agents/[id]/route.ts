/**
 * Agent CRUD API Route
 *
 * BFF endpoint for individual agent operations:
 * - GET: Fetch single agent by ID
 * - PUT: Update existing agent
 * - DELETE: Delete agent
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example GET /api/agents/agent-123
 * @example PUT /api/agents/agent-123 { description: 'Updated description' }
 * @example DELETE /api/agents/agent-123
 */

import { NextRequest, NextResponse } from 'next/server';
import type { AgentDefinition } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

/**
 * GET /api/agents/[id]
 *
 * Fetch a single agent by ID
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/agents/${id}`, {
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
        { error: error.message || 'Failed to fetch agent' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      agent: data.agent as AgentDefinition,
    });
  } catch (error) {
    console.error('Error fetching agent:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * PUT /api/agents/[id]
 *
 * Update an existing agent
 *
 * Request body (all fields optional):
 * {
 *   name?: string,
 *   description?: string,
 *   prompt?: string,
 *   model?: 'sonnet' | 'opus' | 'haiku' | 'inherit',
 *   tools?: string[]
 * }
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await request.json();

    const response = await fetch(`${API_BASE_URL}/agents/${id}`, {
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
        { error: error.message || 'Failed to update agent' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      agent: data.agent as AgentDefinition,
    });
  } catch (error) {
    console.error('Error updating agent:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/agents/[id]
 *
 * Delete an agent
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const response = await fetch(`${API_BASE_URL}/agents/${id}`, {
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
        { error: error.message || 'Failed to delete agent' },
        { status: response.status }
      );
    }

    return NextResponse.json(
      { message: 'Agent deleted successfully' },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error deleting agent:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

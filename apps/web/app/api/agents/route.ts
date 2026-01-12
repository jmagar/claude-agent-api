/**
 * Agents API Route
 *
 * BFF endpoint for agent management:
 * - GET: Fetch all agents
 * - POST: Create a new agent
 *
 * Proxies requests to the backend Claude Agent API.
 *
 * @example GET /api/agents
 * @example POST /api/agents { name: 'my-agent', description: '...', prompt: '...' }
 */

import { NextRequest, NextResponse } from 'next/server';
import type { AgentDefinition } from '@/types';

/**
 * Backend API base URL
 */
const API_BASE_URL =
  process.env.API_BASE_URL || 'http://localhost:54000';

/**
 * GET /api/agents
 *
 * Fetch all agents for the current user
 */
export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/agents`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Forward auth headers if present
        ...(request.headers.get('authorization')
          ? { Authorization: request.headers.get('authorization')! }
          : {}),
      },
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to fetch agents' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      agents: data.agents || [],
    });
  } catch (error) {
    console.error('Error fetching agents:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/agents
 *
 * Create a new agent
 *
 * Request body:
 * {
 *   name: string,
 *   description: string,
 *   prompt: string,
 *   model?: 'sonnet' | 'opus' | 'haiku' | 'inherit',
 *   tools?: string[]
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validate required fields
    if (!body.name || typeof body.name !== 'string') {
      return NextResponse.json(
        { error: 'Name is required and must be a string' },
        { status: 400 }
      );
    }

    if (!body.description || typeof body.description !== 'string') {
      return NextResponse.json(
        { error: 'Description is required and must be a string' },
        { status: 400 }
      );
    }

    if (!body.prompt || typeof body.prompt !== 'string') {
      return NextResponse.json(
        { error: 'Prompt is required and must be a string' },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/agents`, {
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
        prompt: body.prompt,
        model: body.model || 'inherit',
        tools: body.tools || [],
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.message || 'Failed to create agent' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      agent: data.agent as AgentDefinition,
    }, { status: 201 });
  } catch (error) {
    console.error('Error creating agent:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

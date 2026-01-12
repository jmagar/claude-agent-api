/**
 * Tools API Route
 *
 * Returns the built-in tool catalog for the UI.
 */

import { NextResponse } from 'next/server';
import type { ToolDefinition } from '@/types';

const SYSTEM_SERVER = 'system';

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
}

const TOOL_DEFINITIONS: ToolDefinition[] = [
  {
    name: 'Read',
    description: 'Read a file from the workspace.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Write',
    description: 'Write a new file to the workspace.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Edit',
    description: 'Edit a file with a targeted patch.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'MultiEdit',
    description: 'Apply multiple edits to a file in one step.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Bash',
    description: 'Execute a shell command in the workspace.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Glob',
    description: 'List files with glob patterns.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Grep',
    description: 'Search for text within files.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'LS',
    description: 'List files in a directory.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'WebFetch',
    description: 'Fetch data from a URL.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'WebSearch',
    description: 'Search the web for information.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Task',
    description: 'Dispatch a sub-task to another agent.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'TodoWrite',
    description: 'Write or update the task list.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'NotebookEdit',
    description: 'Edit notebook content.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'NotebookRead',
    description: 'Read notebook content.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'AskUserQuestion',
    description: 'Ask the user a clarification question.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'Skill',
    description: 'Invoke an installed skill.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
  {
    name: 'SlashCommand',
    description: 'Run a registered slash command.',
    input_schema: {},
    server: SYSTEM_SERVER,
    enabled: true,
  },
];

export async function GET() {
  return NextResponse.json(TOOL_DEFINITIONS);
}

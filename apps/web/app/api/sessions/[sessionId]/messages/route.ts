/**
 * Session messages API route
 *
 * Fetches messages for a specific session.
 *
 * @see tests/integration/chat-flow.test.tsx for test specifications
 */

import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { sessionId } = await params;

    if (!sessionId) {
      return NextResponse.json(
        { error: "Session ID is required" },
        { status: 400 }
      );
    }

    // Get API key
    const apiKey =
      request.headers.get("x-api-key") || process.env.API_KEY || "";

    if (!apiKey) {
      return NextResponse.json(
        { error: "API key not configured" },
        { status: 401 }
      );
    }

    // Fetch messages from Claude Agent API
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:54000";

    const response = await fetch(`${apiUrl}/sessions/${sessionId}/messages`, {
      headers: {
        "X-API-Key": apiKey,
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        // Session not found, return empty messages
        return NextResponse.json({ messages: [], total: 0 });
      }

      const errorText = await response.text();
      return NextResponse.json(
        {
          error: `API error: ${response.status} ${response.statusText}`,
          details: errorText,
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Fetch messages error:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}

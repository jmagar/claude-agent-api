/**
 * BFF streaming proxy route
 *
 * Proxies SSE streaming requests to Claude Agent API.
 * Handles authentication and error responses.
 *
 * @see tests/integration/chat-flow.test.tsx for test specifications
 */

import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, session_id } = body;

    if (!message) {
      return NextResponse.json(
        { error: "Message is required" },
        { status: 400 }
      );
    }

    // Get API key from headers or environment
    const apiKey =
      request.headers.get("x-api-key") || process.env.API_KEY || "";

    if (!apiKey) {
      return NextResponse.json(
        { error: "API key not configured" },
        { status: 401 }
      );
    }

    // Proxy to Claude Agent API
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:54000";

    const response = await fetch(`${apiUrl}/api/v1/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({
        prompt: message,
        session_id,
        include_partial_messages: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        {
          error: `API error: ${response.status} ${response.statusText}`,
          details: errorText,
        },
        { status: response.status }
      );
    }

    // Return SSE stream
    return new NextResponse(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("Streaming error:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}

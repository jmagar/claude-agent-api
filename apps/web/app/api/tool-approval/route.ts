/**
 * Tool approval API route
 *
 * BFF route for submitting tool approval decisions to the backend.
 */

import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL =
  process.env.API_BASE_URL || "http://localhost:54000/api/v1";

function jsonResponse(body: Record<string, unknown>, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return new NextResponse(JSON.stringify(body), { ...init, headers });
}

export async function POST(request: NextRequest) {
  try {
    const apiKey =
      request.headers.get("X-API-Key") ||
      request.cookies?.get("api-key")?.value;

    if (!apiKey) {
      return jsonResponse(
        { error: { code: "INVALID_API_KEY", message: "API key is required" } },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { tool_use_id, approved, remember } = body ?? {};

    if (!tool_use_id || typeof approved !== "boolean") {
      return jsonResponse(
        {
          error: {
            code: "VALIDATION_ERROR",
            message: "tool_use_id and approved are required",
          },
        },
        { status: 400 }
      );
    }

    const response = await fetch(`${API_BASE_URL}/tool-approval`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify({
        tool_use_id,
        approved,
        remember: Boolean(remember),
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: "Backend request failed" },
      }));

      return jsonResponse(
        {
          error: {
            code: error.error?.code ?? "BACKEND_ERROR",
            message: error.error?.message ?? "Failed to submit tool approval",
          },
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    return jsonResponse(data);
  } catch (error) {
    console.error("Tool approval POST error:", error);
    return jsonResponse(
      {
        error: {
          code: "INTERNAL_ERROR",
          message: error instanceof Error ? error.message : "Internal server error",
        },
      },
      { status: 500 }
    );
  }
}

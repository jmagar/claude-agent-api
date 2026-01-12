import { NextResponse, type NextRequest } from "next/server";
import { logger } from "@/lib/logger";

interface RateLimitState {
  count: number;
  resetAt: number;
}

interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  retryAfterMs: number;
  resetAt: number;
}

const rateLimitStore = new Map<string, RateLimitState>();

function getRateLimitConfig() {
  const windowMs = Number(process.env.RATE_LIMIT_WINDOW_MS ?? 60_000);
  const max = Number(process.env.RATE_LIMIT_MAX ?? 120);

  return {
    windowMs: Number.isFinite(windowMs) ? windowMs : 60_000,
    max: Number.isFinite(max) ? max : 120,
  };
}

export function checkRateLimit(
  key: string,
  limit: number,
  windowMs: number
): RateLimitResult {
  const now = Date.now();
  const existing = rateLimitStore.get(key);

  if (!existing || now >= existing.resetAt) {
    const resetAt = now + windowMs;
    rateLimitStore.set(key, { count: 1, resetAt });
    return {
      allowed: true,
      remaining: Math.max(0, limit - 1),
      retryAfterMs: resetAt - now,
      resetAt,
    };
  }

  if (existing.count >= limit) {
    return {
      allowed: false,
      remaining: 0,
      retryAfterMs: Math.max(0, existing.resetAt - now),
      resetAt: existing.resetAt,
    };
  }

  const nextCount = existing.count + 1;
  rateLimitStore.set(key, { count: nextCount, resetAt: existing.resetAt });

  return {
    allowed: true,
    remaining: Math.max(0, limit - nextCount),
    retryAfterMs: Math.max(0, existing.resetAt - now),
    resetAt: existing.resetAt,
  };
}

export function getApiKey(request: NextRequest): string | null {
  return (
    request.headers.get("x-api-key") ||
    request.headers.get("X-API-Key") ||
    request.cookies.get("api-key")?.value ||
    null
  );
}

export function errorResponse(
  code: string,
  message: string,
  status = 400,
  details?: Record<string, unknown>
) {
  const payload: Record<string, unknown> = { code, message };
  if (details) {
    payload.details = details;
  }

  return NextResponse.json(payload, { status });
}

export function logRequest(request: NextRequest, extra?: Record<string, unknown>) {
  const url = new URL(request.url);
  logger.info("BFF request", {
    method: request.method,
    path: url.pathname,
    ...extra,
  });
}

function getClientKey(request: NextRequest) {
  const apiKey = getApiKey(request);
  if (apiKey) {
    return `api:${apiKey}`;
  }

  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    return `ip:${forwardedFor.split(",")[0].trim()}`;
  }

  return "ip:unknown";
}

export function enforceRateLimit(request: NextRequest) {
  const { windowMs, max } = getRateLimitConfig();
  const key = getClientKey(request);
  const result = checkRateLimit(key, max, windowMs);

  if (result.allowed) {
    return null;
  }

  const response = errorResponse("RATE_LIMITED", "Rate limit exceeded", 429, {
    limit: max,
    windowMs,
    retryAfterMs: result.retryAfterMs,
  });

  response.headers.set("Retry-After", Math.ceil(result.retryAfterMs / 1000).toString());
  response.headers.set("X-RateLimit-Limit", String(max));
  response.headers.set("X-RateLimit-Remaining", String(result.remaining));
  response.headers.set("X-RateLimit-Reset", String(result.resetAt));

  return response;
}

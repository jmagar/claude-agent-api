/**
 * MCP share token helpers
 */

import { createHmac, timingSafeEqual } from "crypto";

const DEFAULT_SECRET = "";

function getShareSecret(): string {
  return process.env.MCP_SHARE_SECRET || DEFAULT_SECRET;
}

function encodePayload(payload: Record<string, unknown>): string {
  return Buffer.from(JSON.stringify(payload)).toString("base64url");
}

function decodePayload(encoded: string): Record<string, unknown> {
  return JSON.parse(Buffer.from(encoded, "base64url").toString("utf8")) as Record<
    string,
    unknown
  >;
}

export function buildShareToken(payload: Record<string, unknown>): string {
  const secret = getShareSecret();
  if (!secret) {
    throw new Error("MCP share secret is not configured");
  }

  const encodedPayload = encodePayload(payload);
  const signature = createHmac("sha256", secret)
    .update(encodedPayload)
    .digest("base64url");

  return `${encodedPayload}.${signature}`;
}

export function parseShareToken(token: string): Record<string, unknown> | null {
  const secret = getShareSecret();
  if (!secret) {
    throw new Error("MCP share secret is not configured");
  }

  const [encodedPayload, signature] = token.split(".");
  if (!encodedPayload || !signature) {
    return null;
  }

  const expectedSignature = createHmac("sha256", secret)
    .update(encodedPayload)
    .digest("base64url");

  const expectedBuffer = Buffer.from(expectedSignature);
  const actualBuffer = Buffer.from(signature);

  if (expectedBuffer.length !== actualBuffer.length) {
    return null;
  }

  if (!timingSafeEqual(expectedBuffer, actualBuffer)) {
    return null;
  }

  try {
    return decodePayload(encodedPayload);
  } catch {
    return null;
  }
}

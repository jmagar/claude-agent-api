/**
 * Correlation ID middleware for request tracking
 */

export function generateCorrelationId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

export function getOrCreateCorrelationId(): string {
  if (typeof window === "undefined") {
    return generateCorrelationId();
  }

  // Check if we already have a correlation ID for this session
  let correlationId = sessionStorage.getItem("correlationId");

  if (!correlationId) {
    correlationId = generateCorrelationId();
    sessionStorage.setItem("correlationId", correlationId);
  }

  return correlationId;
}

export function setCorrelationId(id: string): void {
  if (typeof window !== "undefined") {
    sessionStorage.setItem("correlationId", id);
  }
}

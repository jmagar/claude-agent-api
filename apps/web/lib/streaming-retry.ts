/**
 * Streaming retry utilities
 */

export interface RetryConfig {
  initialDelay: number;
  maxDelay: number;
  maxAttempts: number;
  backoffFactor: number;
  jitterRatio: number;
}

export const defaultRetryConfig: RetryConfig = {
  initialDelay: 100,
  maxDelay: 30000,
  maxAttempts: 10,
  backoffFactor: 2,
  jitterRatio: 0.3,
};

export function calculateRetryDelay(
  attempt: number,
  config: RetryConfig = defaultRetryConfig,
  random: () => number = Math.random
): number {
  const baseDelay = Math.min(
    config.initialDelay * Math.pow(config.backoffFactor, attempt),
    config.maxDelay
  );
  const jitter = baseDelay * config.jitterRatio * random();
  return baseDelay + jitter;
}

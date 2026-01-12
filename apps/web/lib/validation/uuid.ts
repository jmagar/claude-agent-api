/**
 * UUID Validation Utility
 */

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Validates if a string is a valid UUID.
 *
 * @param value - The string to validate
 * @returns True if the string is a valid UUID
 */
export function isUUID(value: string): boolean {
  return typeof value === 'string' && UUID_REGEX.test(value);
}

/**
 * Credential Sanitization Utilities
 *
 * Provides functions to sanitize sensitive credentials from shared configurations
 * (agents, skills, MCP servers, etc.) before generating public share URLs.
 */

/**
 * Patterns to identify sensitive credential fields
 */
const SENSITIVE_FIELD_PATTERNS = [
  /^api[-_]?key$/i,
  /^secret[-_]?key$/i,
  /^access[-_]?token$/i,
  /^refresh[-_]?token$/i,
  /^password$/i,
  /^passwd$/i,
  /^credentials?$/i,
  /^auth[-_]?token$/i,
  /^bearer[-_]?token$/i,
  /^private[-_]?key$/i,
  /^client[-_]?secret$/i,
  /^db[-_]?password$/i,
  /^database[-_]?password$/i,
  /^connection[-_]?string$/i,
  /^dsn$/i,
  /[-_]?key$/i,
  /[-_]?token$/i,
  /[-_]?secret$/i,
  /[-_]?password$/i,
];

/**
 * Replacement text for sanitized credentials
 */
const SANITIZED_PLACEHOLDER = '***REDACTED***';

/**
 * Check if a field name indicates sensitive credential data
 *
 * @param fieldName - Field name to check
 * @returns True if field appears to contain credentials
 */
export function isSensitiveField(fieldName: string): boolean {
  return SENSITIVE_FIELD_PATTERNS.some((pattern) => pattern.test(fieldName));
}

/**
 * Sanitize a single object by removing/redacting sensitive fields
 *
 * @param obj - Object to sanitize
 * @param options - Sanitization options
 * @returns Sanitized copy of object
 */
export function sanitizeObject<T extends Record<string, unknown>>(
  obj: T,
  options: {
    /** Remove sensitive fields entirely (default: false, redacts instead) */
    remove?: boolean;
    /** Additional field names to treat as sensitive */
    additionalSensitiveFields?: string[];
    /** Field names to explicitly preserve (overrides pattern matching) */
    preserveFields?: string[];
  } = {}
): T {
  const { remove = false, additionalSensitiveFields = [], preserveFields = [] } = options;

  const sanitized: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    // Skip if in preserve list
    if (preserveFields.includes(key)) {
      sanitized[key] = value;
      continue;
    }

    // Check if field is sensitive
    const isSensitive =
      isSensitiveField(key) || additionalSensitiveFields.includes(key);

    if (isSensitive) {
      if (!remove) {
        // Redact instead of removing
        sanitized[key] = SANITIZED_PLACEHOLDER;
      }
      // If remove=true, skip adding this field
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // Recursively sanitize nested objects
      sanitized[key] = sanitizeObject(value as Record<string, unknown>, options);
    } else if (Array.isArray(value)) {
      // Recursively sanitize array elements
      sanitized[key] = value.map((item) =>
        typeof item === 'object' && item !== null && !Array.isArray(item)
          ? sanitizeObject(item as Record<string, unknown>, options)
          : item
      );
    } else {
      // Keep non-sensitive primitive values
      sanitized[key] = value;
    }
  }

  return sanitized as T;
}

/**
 * Sanitize agent configuration for sharing
 *
 * @param agent - Agent definition
 * @returns Sanitized agent configuration
 */
export function sanitizeAgentConfig(agent: {
  name: string;
  description: string;
  prompt: string;
  model?: string;
  tools?: string[];
  [key: string]: unknown;
}): Record<string, unknown> {
  // Remove internal IDs and timestamps, sanitize any credential-like fields
  const { id, created_at, updated_at, is_shared, share_url, ...config } = agent as Record<
    string,
    unknown
  >;

  return sanitizeObject(config, {
    preserveFields: ['name', 'description', 'prompt', 'model', 'tools'],
  });
}

/**
 * Sanitize skill configuration for sharing
 *
 * @param skill - Skill definition
 * @returns Sanitized skill configuration
 */
export function sanitizeSkillConfig(skill: {
  name: string;
  description: string;
  content: string;
  [key: string]: unknown;
}): Record<string, unknown> {
  const { id, created_at, updated_at, is_shared, share_url, ...config } = skill as Record<
    string,
    unknown
  >;

  return sanitizeObject(config, {
    preserveFields: ['name', 'description', 'content'],
  });
}

/**
 * Sanitize MCP server configuration for sharing
 *
 * @param server - MCP server configuration
 * @returns Sanitized server configuration
 */
export function sanitizeMcpServerConfig(server: {
  name: string;
  type: string;
  command?: string;
  args?: string[];
  url?: string;
  env?: Record<string, string>;
  headers?: Record<string, string>;
  [key: string]: unknown;
}): Record<string, unknown> {
  const {
    id,
    status,
    error,
    created_at,
    updated_at,
    tools_count,
    resources_count,
    ...config
  } = server as Record<string, unknown>;

  // Sanitize environment variables and headers
  const sanitized = sanitizeObject(config, {
    preserveFields: ['name', 'type', 'command', 'args', 'url'],
    additionalSensitiveFields: ['env', 'headers'],
  });

  // Specifically redact all env vars and headers
  if (sanitized.env && typeof sanitized.env === 'object') {
    const envObj = sanitized.env as Record<string, unknown>;
    sanitized.env = Object.fromEntries(
      Object.keys(envObj).map((key) => [key, SANITIZED_PLACEHOLDER])
    );
  }

  if (sanitized.headers && typeof sanitized.headers === 'object') {
    const headersObj = sanitized.headers as Record<string, unknown>;
    sanitized.headers = Object.fromEntries(
      Object.keys(headersObj).map((key) => [key, SANITIZED_PLACEHOLDER])
    );
  }

  return sanitized;
}

/**
 * Sanitize slash command configuration for sharing
 *
 * @param command - Slash command definition
 * @returns Sanitized command configuration
 */
export function sanitizeSlashCommandConfig(command: {
  name: string;
  description: string;
  content: string;
  enabled?: boolean;
  [key: string]: unknown;
}): Record<string, unknown> {
  const { id, created_at, updated_at, ...config } = command as Record<string, unknown>;

  return sanitizeObject(config, {
    preserveFields: ['name', 'description', 'content', 'enabled'],
  });
}

/**
 * Validate that all sensitive fields have been sanitized
 *
 * @param obj - Object to validate
 * @returns Validation result
 */
export function validateSanitization(obj: Record<string, unknown>): {
  isSanitized: boolean;
  unsanitizedFields: string[];
} {
  const unsanitized: string[] = [];

  function checkObject(o: Record<string, unknown>, prefix = ''): void {
    for (const [key, value] of Object.entries(o)) {
      const fullKey = prefix ? `${prefix}.${key}` : key;

      if (isSensitiveField(key)) {
        // Check if value looks like a credential (not redacted)
        if (
          typeof value === 'string' &&
          value !== SANITIZED_PLACEHOLDER &&
          value.length > 0
        ) {
          unsanitized.push(fullKey);
        }
      }

      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        checkObject(value as Record<string, unknown>, fullKey);
      } else if (Array.isArray(value)) {
        value.forEach((item, index) => {
          if (typeof item === 'object' && item !== null && !Array.isArray(item)) {
            checkObject(item as Record<string, unknown>, `${fullKey}[${index}]`);
          }
        });
      }
    }
  }

  checkObject(obj);

  return {
    isSanitized: unsanitized.length === 0,
    unsanitizedFields: unsanitized,
  };
}

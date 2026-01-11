/**
 * MCP Server Form Validation
 *
 * Zod schemas and validation utilities for MCP server configuration forms.
 * Provides type-safe validation with clear error messages for different transport types.
 *
 * @module lib/validation/mcp-server
 */

import { z } from 'zod';
import type { McpTransportType } from '@/types';

/**
 * Validation schema for stdio transport
 */
const stdioSchema = z.object({
  name: z
    .string()
    .min(1, 'Server name is required')
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      'Server name can only contain letters, numbers, hyphens, and underscores'
    ),
  type: z.literal('stdio'),
  command: z.string().min(1, 'Command is required'),
  args: z
    .string()
    .transform((val, ctx) => {
      try {
        const parsed = JSON.parse(val);
        if (!Array.isArray(parsed)) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: 'Arguments must be a valid JSON array',
          });
          return z.NEVER;
        }
        return parsed;
      } catch {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Invalid JSON format',
        });
        return z.NEVER;
      }
    }),
  env: z.record(z.string()).optional(),
  enabled: z.boolean().default(true),
});

/**
 * Validation schema for SSE transport
 */
const sseSchema = z.object({
  name: z
    .string()
    .min(1, 'Server name is required')
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      'Server name can only contain letters, numbers, hyphens, and underscores'
    ),
  type: z.literal('sse'),
  url: z
    .string()
    .min(1, 'URL is required')
    .url('Invalid URL format')
    .refine(
      (url) => url.startsWith('http://') || url.startsWith('https://'),
      'URL must start with http:// or https://'
    ),
  env: z.record(z.string()).optional(),
  enabled: z.boolean().default(true),
});

/**
 * Validation schema for HTTP transport
 */
const httpSchema = z.object({
  name: z
    .string()
    .min(1, 'Server name is required')
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      'Server name can only contain letters, numbers, hyphens, and underscores'
    ),
  type: z.literal('http'),
  url: z
    .string()
    .min(1, 'URL is required')
    .url('Invalid URL format')
    .refine(
      (url) => url.startsWith('http://') || url.startsWith('https://'),
      'URL must start with http:// or https://'
    ),
  headers: z.record(z.string()).optional(),
  env: z.record(z.string()).optional(),
  enabled: z.boolean().default(true),
});

/**
 * Discriminated union schema for all transport types
 */
export const mcpServerFormSchema = z.discriminatedUnion('type', [
  stdioSchema,
  sseSchema,
  httpSchema,
]);

/**
 * Validation result type
 */
export interface ValidationResult {
  success: boolean;
  data?: z.infer<typeof mcpServerFormSchema>;
  errors?: Record<string, string>;
}

/**
 * Validates MCP server form data
 *
 * @param formData - Form data to validate
 * @param existingNames - List of existing server names (for uniqueness check)
 * @param isEditMode - Whether form is in edit mode (skips uniqueness check)
 * @returns Validation result with success flag, parsed data, or error messages
 *
 * @example
 * ```ts
 * const result = validateMcpServerForm({
 *   name: 'postgres',
 *   type: 'stdio',
 *   command: 'npx',
 *   args: '["@modelcontextprotocol/server-postgres"]',
 *   enabled: true
 * }, ['filesystem'], false);
 *
 * if (result.success) {
 *   console.log('Valid data:', result.data);
 * } else {
 *   console.error('Errors:', result.errors);
 * }
 * ```
 */
export function validateMcpServerForm(
  formData: unknown,
  existingNames: string[] = [],
  isEditMode = false
): ValidationResult {
  // First check name uniqueness (before Zod validation)
  if (!isEditMode && typeof formData === 'object' && formData !== null) {
    const data = formData as Record<string, unknown>;
    if (
      typeof data.name === 'string' &&
      existingNames.includes(data.name.trim())
    ) {
      return {
        success: false,
        errors: {
          name: 'Server name already exists',
        },
      };
    }
  }

  // Run Zod validation
  const result = mcpServerFormSchema.safeParse(formData);

  if (result.success) {
    return {
      success: true,
      data: result.data,
    };
  }

  // Transform Zod errors to field-specific error messages
  const errors: Record<string, string> = {};

  for (const issue of result.error.issues) {
    const fieldPath = issue.path.join('.');
    const fieldName = fieldPath || 'form';

    // Use first error message for each field
    if (!errors[fieldName]) {
      errors[fieldName] = issue.message;
    }
  }

  return {
    success: false,
    errors,
  };
}

/**
 * Type guard to check if form data is valid stdio config
 */
export function isStdioConfig(
  data: unknown
): data is z.infer<typeof stdioSchema> {
  return stdioSchema.safeParse(data).success;
}

/**
 * Type guard to check if form data is valid SSE config
 */
export function isSseConfig(data: unknown): data is z.infer<typeof sseSchema> {
  return sseSchema.safeParse(data).success;
}

/**
 * Type guard to check if form data is valid HTTP config
 */
export function isHttpConfig(
  data: unknown
): data is z.infer<typeof httpSchema> {
  return httpSchema.safeParse(data).success;
}

/**
 * Validates transport type value
 */
export function isValidTransportType(type: unknown): type is McpTransportType {
  return (
    typeof type === 'string' && ['stdio', 'sse', 'http'].includes(type)
  );
}

/**
 * Gets validation schema for specific transport type
 */
export function getSchemaForTransportType(type: McpTransportType) {
  switch (type) {
    case 'stdio':
      return stdioSchema;
    case 'sse':
      return sseSchema;
    case 'http':
      return httpSchema;
  }
}

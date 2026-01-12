/**
 * PlateJsonEditor Component
 *
 * JSON-specific editor with validation for MCP Server arguments.
 * Provides JSON parsing validation and optional Zod schema validation.
 */

'use client';

import * as React from 'react';
import type { z } from 'zod';
import { PlateEditor } from './PlateEditor';
import { Button } from '@/components/ui/button';
import type { SlateValue } from '@/lib/slate-serializers';

export interface PlateJsonEditorProps {
  value: string;
  onChange: (value: string) => void;
  schema?: z.ZodSchema;
  ariaLabel?: string;
  placeholder?: string;
}

interface JsonValidationResult {
  isValid: boolean;
  error?: string;
  parsed?: unknown;
}

/**
 * Validate JSON string with JSON.parse
 */
function validateJson(jsonString: string): JsonValidationResult {
  try {
    const parsed = JSON.parse(jsonString);
    return { isValid: true, parsed };
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Invalid JSON';
    return { isValid: false, error: message };
  }
}

/**
 * Validate parsed JSON against Zod schema
 */
function validateSchema(parsed: unknown, schema?: z.ZodSchema): JsonValidationResult {
  if (!schema) {
    return { isValid: true, parsed };
  }

  try {
    schema.parse(parsed);
    return { isValid: true, parsed };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Schema validation failed';
    return { isValid: false, error: message };
  }
}

/**
 * Convert JSON string to Slate value (code_block node)
 */
function jsonToSlate(jsonString: string): SlateValue {
  return [
    {
      type: 'code_block',
      lang: 'json',
      children: [{ text: jsonString }],
    },
  ];
}

/**
 * Extract JSON string from Slate value (code_block node)
 */
function slateToJson(slateValue: SlateValue): string {
  if (slateValue.length === 0) {
    return '';
  }

  const firstNode = slateValue[0];
  if (firstNode.type !== 'code_block') {
    return '';
  }

  const codeBlock = firstNode as { type: 'code_block'; children: Array<{ text: string }> };
  return codeBlock.children[0]?.text || '';
}

/**
 * PlateJsonEditor - JSON-specific editor with validation
 *
 * Features:
 * - Code block editor with JSON syntax highlighting
 * - Real-time JSON.parse validation
 * - Optional Zod schema validation
 * - Format button to prettify JSON
 *
 * @param props - PlateJsonEditorProps
 * @returns React component
 */
export function PlateJsonEditor({
  value,
  onChange,
  schema,
  ariaLabel = 'JSON editor',
  placeholder = 'Enter JSON...',
}: PlateJsonEditorProps) {
  // Convert JSON string to Slate value
  const slateValue = React.useMemo(() => jsonToSlate(value), [value]);

  // Validate JSON and schema
  const validation = React.useMemo(() => {
    const jsonResult = validateJson(value);
    if (!jsonResult.isValid) {
      return jsonResult;
    }

    const schemaResult = validateSchema(jsonResult.parsed, schema);
    return schemaResult;
  }, [value, schema]);

  // Handle editor changes
  const handleSlateChange = React.useCallback(
    (newSlateValue: SlateValue) => {
      const jsonString = slateToJson(newSlateValue);
      onChange(jsonString);
    },
    [onChange]
  );

  // Handle Format button click
  const handleFormat = React.useCallback(() => {
    if (!validation.isValid || !validation.parsed) {
      return;
    }

    try {
      const formatted = JSON.stringify(validation.parsed, null, 2);
      onChange(formatted);
    } catch {
      // Ignore format errors
    }
  }, [validation, onChange]);

  return (
    <div className="space-y-2" aria-label={ariaLabel}>
      {/* Editor */}
      <PlateEditor
        value={slateValue}
        onChange={handleSlateChange}
        placeholder={placeholder}
        ariaLabel={ariaLabel}
        minHeight="200px"
      />

      {/* Validation Error */}
      {!validation.isValid && validation.error && (
        <div role="alert" className="text-sm text-red-600">
          {validation.error}
        </div>
      )}

      {/* Format Button */}
      <div className="flex justify-end">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleFormat}
          disabled={!validation.isValid}
          aria-label="Format JSON"
        >
          Format
        </Button>
      </div>
    </div>
  );
}

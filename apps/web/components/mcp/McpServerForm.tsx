/**
 * McpServerForm Component
 *
 * Form for creating and editing MCP server configurations with:
 * - Transport type selection (stdio, sse, http)
 * - Dynamic field visibility based on transport type
 * - JSON editor for arguments array
 * - Environment variables editor
 * - HTTP headers editor (for http transport)
 * - Form validation
 * - Loading states during submission
 *
 * @example
 * ```tsx
 * <McpServerForm
 *   server={existingServer} // Optional for edit mode
 *   existingNames={['postgres', 'filesystem']}
 *   onSubmit={handleSubmit}
 *   onCancel={handleCancel}
 * />
 * ```
 */

'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { XIcon, PlusIcon } from 'lucide-react';
import { PlateJsonEditor } from '@/components/plate';
import type { McpServerConfig, McpTransportType } from '@/types';
import { validateMcpServerForm } from '@/lib/validation/mcp-server';
import { z } from 'zod';

/**
 * Zod schema for MCP server arguments (JSON array of strings)
 */
const mcpArgsSchema = z.array(z.string());

export interface McpServerFormProps {
  /**
   * Existing server to edit (omit for create mode)
   */
  server?: McpServerConfig;

  /**
   * List of existing server names (for validation)
   */
  existingNames?: string[];

  /**
   * Callback when form is submitted
   * @param data - The server configuration data
   */
  onSubmit: (data: Partial<McpServerConfig>) => void | Promise<void>;

  /**
   * Callback when form is cancelled
   */
  onCancel: () => void;
}

interface EnvVar {
  key: string;
  value: string;
}

interface Header {
  key: string;
  value: string;
}

export function McpServerForm({
  server,
  existingNames = [],
  onSubmit,
  onCancel,
}: McpServerFormProps) {
  const isEditMode = !!server;

  // Form state
  const [name, setName] = useState(server?.name ?? '');
  const [type, setType] = useState<McpTransportType>(server?.transport_type ?? 'stdio');
  const [command, setCommand] = useState(server?.command ?? '');
  const [args, setArgs] = useState(
    server?.args ? JSON.stringify(server.args, null, 2) : '[]'
  );
  const [url, setUrl] = useState(server?.url ?? '');
  const [envVars, setEnvVars] = useState<EnvVar[]>(
    server?.env
      ? Object.entries(server.env).map(([key, value]) => ({ key, value: value as string }))
      : []
  );
  const [headers, setHeaders] = useState<Header[]>(
    server?.headers
      ? Object.entries(server.headers).map(([key, value]) => ({ key, value: value as string }))
      : []
  );
  const [enabled, setEnabled] = useState(server?.enabled ?? true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  /**
   * Validate form using extracted validation utility
   */
  const validate = (): boolean => {
    // Prepare form data based on transport type
    const formData: Record<string, unknown> = {
      name: name.trim(),
      type,
      enabled,
    };

    // Add transport-specific fields
    if (type === 'stdio') {
      formData.command = command.trim();
      formData.args = args; // Will be validated and parsed by Zod
    } else {
      formData.url = url.trim();
    }

    // Add headers for http transport
    if (type === 'http' && headers.length > 0) {
      formData.headers = headers.reduce(
        (acc, { key, value }) => {
          if (key.trim()) {
            acc[key.trim()] = value;
          }
          return acc;
        },
        {} as Record<string, string>
      );
    }

    // Add environment variables
    if (envVars.length > 0) {
      formData.env = envVars.reduce(
        (acc, { key, value }) => {
          if (key.trim()) {
            acc[key.trim()] = value;
          }
          return acc;
        },
        {} as Record<string, string>
      );
    }

    // Validate using Zod schema
    const result = validateMcpServerForm(formData, existingNames, isEditMode);

    if (result.success) {
      setErrors({});
      return true;
    }

    setErrors(result.errors || {});
    return false;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const data: Partial<McpServerConfig> = {
        name: name.trim(),
        transport_type: type,
        enabled,
      };

      // Add transport-specific fields
      if (type === 'stdio') {
        data.command = command.trim();
        data.args = JSON.parse(args);
      } else {
        data.url = url.trim();
      }

      // Add headers for http transport
      if (type === 'http' && headers.length > 0) {
        data.headers = headers.reduce(
          (acc, { key, value }) => {
            if (key.trim()) {
              acc[key.trim()] = value;
            }
            return acc;
          },
          {} as Record<string, string>
        );
      }

      // Add environment variables
      if (envVars.length > 0) {
        data.env = envVars.reduce(
          (acc, { key, value }) => {
            if (key.trim()) {
              acc[key.trim()] = value;
            }
            return acc;
          },
          {} as Record<string, string>
        );
      }

      await onSubmit(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Environment variable handlers
  const addEnvVar = () => {
    setEnvVars([...envVars, { key: '', value: '' }]);
  };

  const updateEnvVar = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...envVars];
    updated[index][field] = value;
    setEnvVars(updated);
  };

  const removeEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  // Header handlers
  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }]);
  };

  const updateHeader = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...headers];
    updated[index][field] = value;
    setHeaders(updated);
  };

  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-4">
          {isEditMode ? 'Edit MCP Server' : 'Add MCP Server'}
        </h2>
      </div>

      {/* Server Name */}
      <div className="space-y-2">
        <Label htmlFor="name">Server Name</Label>
        <Input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., postgres, filesystem"
          disabled={isEditMode}
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? 'name-error' : undefined}
        />
        {errors.name && (
          <p id="name-error" className="text-sm text-destructive" role="alert">
            {errors.name}
          </p>
        )}
      </div>

      {/* Transport Type */}
      <div className="space-y-2">
        <Label htmlFor="type">Transport Type</Label>
        <Select
          value={type}
          onValueChange={(value) => setType(value as McpTransportType)}
        >
          <SelectTrigger id="type">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="stdio">stdio (Local process)</SelectItem>
            <SelectItem value="sse">SSE (Server-Sent Events)</SelectItem>
            <SelectItem value="http">HTTP (REST API)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* stdio fields */}
      {type === 'stdio' && (
        <>
          <div className="space-y-2">
            <Label htmlFor="command">Command</Label>
            <Input
              id="command"
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="e.g., npx, node, python"
              aria-invalid={!!errors.command}
              aria-describedby={errors.command ? 'command-error' : undefined}
            />
            {errors.command && (
              <p id="command-error" className="text-sm text-destructive" role="alert">
                {errors.command}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="args">Arguments (JSON array)</Label>
            <PlateJsonEditor
              value={args}
              onChange={setArgs}
              schema={mcpArgsSchema}
              placeholder='["-y", "@modelcontextprotocol/server-postgres"]'
              ariaLabel="MCP server arguments"
            />
            {errors.args && (
              <p id="args-error" className="text-sm text-destructive" role="alert">
                {errors.args}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Must be a valid JSON array, e.g., ["arg1", "arg2"]
            </p>
          </div>
        </>
      )}

      {/* SSE/HTTP fields */}
      {(type === 'sse' || type === 'http') && (
        <div className="space-y-2">
          <Label htmlFor="url">URL</Label>
          <Input
            id="url"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/mcp"
            aria-invalid={!!errors.url}
            aria-describedby={errors.url ? 'url-error' : undefined}
          />
          {errors.url && (
            <p id="url-error" className="text-sm text-destructive" role="alert">
              {errors.url}
            </p>
          )}
        </div>
      )}

      {/* HTTP headers */}
      {type === 'http' && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Headers</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addHeader}
            >
              <PlusIcon className="h-4 w-4 mr-1" />
              Add Header
            </Button>
          </div>
          {headers.length === 0 && (
            <p className="text-sm text-muted-foreground">No headers configured</p>
          )}
          <div className="space-y-2">
            {headers.map((header, index) => (
              <div key={index} className="flex items-center gap-2">
                <Input
                  type="text"
                  value={header.key}
                  onChange={(e) => updateHeader(index, 'key', e.target.value)}
                  placeholder="Header key"
                  className="flex-1"
                />
                <Input
                  type="text"
                  value={header.value}
                  onChange={(e) => updateHeader(index, 'value', e.target.value)}
                  placeholder="Header value"
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeHeader(index)}
                  aria-label="Remove header"
                >
                  <XIcon className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Environment Variables */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label>Environment Variables</Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addEnvVar}
          >
            <PlusIcon className="h-4 w-4 mr-1" />
            Add Variable
          </Button>
        </div>
        {envVars.length === 0 && (
          <p className="text-sm text-muted-foreground">No environment variables</p>
        )}
        <div className="space-y-2">
          {envVars.map((envVar, index) => (
            <div key={index} className="flex items-center gap-2">
              <Input
                type="text"
                value={envVar.key}
                onChange={(e) => updateEnvVar(index, 'key', e.target.value)}
                placeholder="Key"
                className="flex-1"
              />
              <Input
                type="text"
                value={envVar.value}
                onChange={(e) => updateEnvVar(index, 'value', e.target.value)}
                placeholder="Value"
                className="flex-1"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => removeEnvVar(index)}
                aria-label="Remove variable"
              >
                <XIcon className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      </div>

      {/* Enabled Toggle */}
      <div className="flex items-center justify-between">
        <Label htmlFor="enabled">Enabled</Label>
        <Switch
          id="enabled"
          checked={enabled}
          onCheckedChange={setEnabled}
          aria-label="Enable or disable this server"
        />
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting
            ? 'Saving...'
            : isEditMode
            ? 'Save Changes'
            : 'Create Server'}
        </Button>
      </div>
    </form>
  );
}

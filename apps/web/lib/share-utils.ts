/**
 * Share Utilities
 *
 * Utilities for downloading and copying shared configurations
 * (agents, skills, MCP servers, slash commands).
 */

/**
 * Copy text to clipboard
 *
 * @param text - Text to copy
 * @returns Promise that resolves when text is copied
 */
export async function copyToClipboard(text: string): Promise<void> {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
  } catch (error) {
    throw new Error(
      `Failed to copy to clipboard: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Download text content as a file
 *
 * @param content - Content to download
 * @param filename - Filename for downloaded file
 * @param mimeType - MIME type of the content (default: text/plain)
 */
export function downloadAsFile(
  content: string,
  filename: string,
  mimeType: string = 'text/plain'
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();

  // Clean up
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Download JSON object as a file
 *
 * @param obj - Object to download
 * @param filename - Filename for downloaded file (default: includes .json extension)
 */
export function downloadAsJson(obj: unknown, filename: string): void {
  const jsonContent = JSON.stringify(obj, null, 2);
  const filenameWithExt = filename.endsWith('.json') ? filename : `${filename}.json`;
  downloadAsFile(jsonContent, filenameWithExt, 'application/json');
}

/**
 * Download YAML content as a file
 *
 * @param content - YAML content to download
 * @param filename - Filename for downloaded file (default: includes .yaml extension)
 */
export function downloadAsYaml(content: string, filename: string): void {
  const filenameWithExt = filename.endsWith('.yaml') || filename.endsWith('.yml')
    ? filename
    : `${filename}.yaml`;
  downloadAsFile(content, filenameWithExt, 'text/yaml');
}

/**
 * Download markdown content as a file
 *
 * @param content - Markdown content to download
 * @param filename - Filename for downloaded file (default: includes .md extension)
 */
export function downloadAsMarkdown(content: string, filename: string): void {
  const filenameWithExt = filename.endsWith('.md') ? filename : `${filename}.md`;
  downloadAsFile(content, filenameWithExt, 'text/markdown');
}

/**
 * Generate shareable configuration in multiple formats
 *
 * @param config - Configuration object
 * @param name - Name for the configuration
 * @returns Configuration in different formats
 */
export function generateShareFormats(
  config: Record<string, unknown>,
  name: string
): {
  json: string;
  yaml: string;
  url: string;
} {
  const json = JSON.stringify(config, null, 2);

  // Simple YAML generation (for complex YAML, use js-yaml library)
  const yaml = Object.entries(config)
    .map(([key, value]) => {
      if (typeof value === 'string') {
        return `${key}: "${value}"`;
      } else if (typeof value === 'object' && value !== null) {
        return `${key}:\n  ${JSON.stringify(value, null, 2).split('\n').join('\n  ')}`;
      }
      return `${key}: ${value}`;
    })
    .join('\n');

  // Generate base64-encoded URL parameter
  const encoded = btoa(encodeURIComponent(json));
  const url = `${window.location.origin}/import?config=${encoded}&name=${encodeURIComponent(name)}`;

  return { json, yaml, url };
}

/**
 * Copy share URL to clipboard with visual feedback
 *
 * @param url - URL to copy
 * @param onSuccess - Callback for success
 * @param onError - Callback for error
 */
export async function copyShareUrl(
  url: string,
  onSuccess?: () => void,
  onError?: (error: Error) => void
): Promise<void> {
  try {
    await copyToClipboard(url);
    onSuccess?.();
  } catch (error) {
    onError?.(error instanceof Error ? error : new Error('Failed to copy'));
  }
}

/**
 * Create a shareable link element
 *
 * @param url - Share URL
 * @returns HTML anchor element with share URL
 */
export function createShareLink(url: string): HTMLAnchorElement {
  const link = document.createElement('a');
  link.href = url;
  link.textContent = url;
  link.className = 'text-blue-600 hover:underline break-all';
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  return link;
}

/**
 * Format file size for display
 *
 * @param bytes - Size in bytes
 * @returns Formatted string (e.g., "1.5 KB", "2.3 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Validate share URL format
 *
 * @param url - URL to validate
 * @returns True if URL appears to be a valid share URL
 */
export function isValidShareUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return (
      parsed.protocol === 'http:' ||
      parsed.protocol === 'https:' &&
      parsed.pathname.includes('/share/')
    );
  } catch {
    return false;
  }
}

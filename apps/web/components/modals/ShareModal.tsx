/**
 * ShareModal Component
 *
 * Modal for sharing MCP server configurations with:
 * - Share link generation
 * - Copy to clipboard functionality
 * - Public/private toggle (future)
 * - Credential sanitization notice
 * - Share URL display
 *
 * @example
 * ```tsx
 * <ShareModal
 *   isOpen={showShare}
 *   onClose={() => setShowShare(false)}
 *   serverName="postgres"
 *   serverConfig={mcpServerConfig}
 * />
 * ```
 */

'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  CopyIcon,
  CheckIcon,
  Share2Icon,
  AlertTriangleIcon,
  LoaderIcon,
} from 'lucide-react';
import type { McpServerConfig } from '@/types';

export interface ShareModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;

  /**
   * Callback when modal is closed
   */
  onClose: () => void;

  /**
   * Name of the server to share
   */
  serverName: string;

  /**
   * Server configuration (optional, for preview)
   */
  serverConfig?: McpServerConfig;
}

export function ShareModal({
  isOpen,
  onClose,
  serverName,
  serverConfig,
}: ShareModalProps) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [shareToken, setShareToken] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setShareUrl(null);
      setShareToken(null);
      setIsCopied(false);
      setError(null);
      // Auto-generate share link when modal opens
      generateShareLink();
    }
  }, [isOpen, serverName]);

  /**
   * Generate share link for the server
   */
  const generateShareLink = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/mcp-servers/${encodeURIComponent(serverName)}/share`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          error: { message: 'Failed to generate share link' },
        }));
        throw new Error(errorData.error?.message ?? 'Failed to generate share link');
      }

      const data = await response.json();
      setShareUrl(data.share_url);
      setShareToken(data.share_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate share link');
    } finally {
      setIsGenerating(false);
    }
  };

  /**
   * Copy share link to clipboard
   */
  const copyToClipboard = async () => {
    if (!shareUrl) return;

    try {
      await navigator.clipboard.writeText(shareUrl);
      setIsCopied(true);

      // Reset copied state after 2 seconds
      setTimeout(() => {
        setIsCopied(false);
      }, 2000);
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share2Icon className="h-5 w-5" />
            Share MCP Server
          </DialogTitle>
          <DialogDescription>
            Share the <span className="font-semibold">{serverName}</span> MCP server
            configuration with others
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Security notice */}
          <Alert>
            <AlertTriangleIcon className="h-4 w-4" />
            <AlertDescription className="text-sm">
              <strong>Security Notice:</strong> Sensitive credentials (API keys, passwords,
              tokens) will be redacted from the shared configuration.
            </AlertDescription>
          </Alert>

          {/* Error state */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription className="text-sm">{error}</AlertDescription>
            </Alert>
          )}

          {/* Loading state */}
          {isGenerating && (
            <div className="flex items-center justify-center p-6">
              <LoaderIcon className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">
                Generating share link...
              </span>
            </div>
          )}

          {/* Share link display */}
          {shareUrl && !isGenerating && (
            <div className="space-y-2">
              <Label htmlFor="share-url">Share Link</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="share-url"
                  type="text"
                  value={shareUrl}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={copyToClipboard}
                  className="shrink-0"
                  aria-label="Copy share link"
                >
                  {isCopied ? (
                    <CheckIcon className="h-4 w-4 text-green-600" />
                  ) : (
                    <CopyIcon className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {isCopied && (
                <p className="text-xs text-green-600">Copied to clipboard!</p>
              )}
            </div>
          )}

          {/* Server info (optional preview) */}
          {serverConfig && shareUrl && (
            <div className="mt-4 p-3 bg-muted rounded-md">
              <p className="text-xs text-muted-foreground mb-2">Configuration Preview:</p>
              <div className="space-y-1 text-xs">
                <p>
                  <span className="font-medium">Type:</span> {serverConfig.type}
                </p>
                {serverConfig.command && (
                  <p>
                    <span className="font-medium">Command:</span> {serverConfig.command}
                  </p>
                )}
                {serverConfig.url && (
                  <p>
                    <span className="font-medium">URL:</span> {serverConfig.url}
                  </p>
                )}
                <p>
                  <span className="font-medium">Tools:</span> {serverConfig.tools_count ?? 0}
                </p>
                <p>
                  <span className="font-medium">Resources:</span>{' '}
                  {serverConfig.resources_count ?? 0}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 mt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            Close
          </Button>
          {shareUrl && (
            <Button type="button" onClick={copyToClipboard}>
              {isCopied ? (
                <>
                  <CheckIcon className="h-4 w-4 mr-2" />
                  Copied
                </>
              ) : (
                <>
                  <CopyIcon className="h-4 w-4 mr-2" />
                  Copy Link
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

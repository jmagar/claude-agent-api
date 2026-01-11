/**
 * MCP Servers Settings Page
 *
 * Main settings page for managing MCP (Model Context Protocol) servers.
 * Provides UI for:
 * - Listing all configured MCP servers
 * - Adding new servers via modal form
 * - Editing existing servers
 * - Deleting servers with confirmation
 * - Sharing server configurations
 *
 * Route: /settings/mcp-servers
 */

'use client';

import { useState } from 'react';
import { McpServerList } from '@/components/mcp/McpServerList';
import { McpServerForm } from '@/components/mcp/McpServerForm';
import { ShareModal } from '@/components/modals/ShareModal';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/useToast';
import { useMcpServers } from '@/hooks/useMcpServers';
import type { McpServerConfig } from '@/types';

export default function McpServersPage() {
  const { toast } = useToast();
  const { servers, createServer, updateServer, deleteServer } = useMcpServers();

  // Modal states
  const [showForm, setShowForm] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Current operation states
  const [editingServer, setEditingServer] = useState<McpServerConfig | null>(null);
  const [sharingServer, setSharingServer] = useState<McpServerConfig | null>(null);
  const [deletingServerName, setDeletingServerName] = useState<string | null>(null);

  /**
   * Handle adding a new server
   */
  const handleAdd = () => {
    setEditingServer(null);
    setShowForm(true);
  };

  /**
   * Handle editing an existing server
   */
  const handleEdit = (server: McpServerConfig) => {
    setEditingServer(server);
    setShowForm(true);
  };

  /**
   * Handle form submission (create or update)
   */
  const handleSubmit = async (data: Partial<McpServerConfig>) => {
    try {
      if (editingServer) {
        // Update existing server
        await updateServer(editingServer.name, data);
        toast({
          title: 'Server updated',
          description: `MCP server "${editingServer.name}" has been updated successfully.`,
        });
      } else {
        // Create new server
        await createServer(data);
        toast({
          title: 'Server created',
          description: `MCP server "${data.name}" has been created successfully.`,
        });
      }

      setShowForm(false);
      setEditingServer(null);
    } catch (error) {
      toast({
        title: 'Error',
        description:
          error instanceof Error
            ? error.message
            : 'Failed to save MCP server configuration',
        variant: 'destructive',
      });
    }
  };

  /**
   * Handle delete button click (show confirmation)
   */
  const handleDeleteClick = (name: string) => {
    setDeletingServerName(name);
    setShowDeleteConfirm(true);
  };

  /**
   * Handle delete confirmation
   */
  const handleDeleteConfirm = async () => {
    if (!deletingServerName) return;

    try {
      await deleteServer(deletingServerName);
      toast({
        title: 'Server deleted',
        description: `MCP server "${deletingServerName}" has been deleted.`,
      });
      setShowDeleteConfirm(false);
      setDeletingServerName(null);
    } catch (error) {
      toast({
        title: 'Error',
        description:
          error instanceof Error ? error.message : 'Failed to delete MCP server',
        variant: 'destructive',
      });
    }
  };

  /**
   * Handle share button click
   */
  const handleShare = (server: McpServerConfig) => {
    setSharingServer(server);
    setShowShare(true);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">MCP Servers</h1>
        <p className="text-muted-foreground">
          Manage Model Context Protocol servers that provide tools and resources for Claude to
          interact with external systems.
        </p>
      </div>

      {/* Server list */}
      <McpServerList
        onAdd={handleAdd}
        onEdit={handleEdit}
        onDelete={handleDeleteClick}
        onShare={handleShare}
      />

      {/* Add/Edit Server Modal */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingServer ? 'Edit MCP Server' : 'Add MCP Server'}
            </DialogTitle>
            <DialogDescription>
              {editingServer
                ? `Update configuration for ${editingServer.name}`
                : 'Configure a new MCP server to provide tools and resources'}
            </DialogDescription>
          </DialogHeader>
          <McpServerForm
            server={editingServer ?? undefined}
            existingNames={
              servers
                ?.filter((s) => s.name !== editingServer?.name)
                .map((s) => s.name) ?? []
            }
            onSubmit={handleSubmit}
            onCancel={() => {
              setShowForm(false);
              setEditingServer(null);
            }}
          />
        </DialogContent>
      </Dialog>

      {/* Share Modal */}
      {sharingServer && (
        <ShareModal
          isOpen={showShare}
          onClose={() => {
            setShowShare(false);
            setSharingServer(null);
          }}
          serverName={sharingServer.name}
          serverConfig={sharingServer}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the MCP server configuration for "
              {deletingServerName}". This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setShowDeleteConfirm(false);
                setDeletingServerName(null);
              }}
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteConfirm}>
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

'use client';

import { useState, useMemo } from 'react';
import type { SlashCommand } from '@/types';

interface SlashCommandListProps {
  commands: SlashCommand[];
  onEdit: (command: SlashCommand) => void;
  onDelete: (id: string) => void;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  onCreate?: () => void;
  isLoading?: boolean;
  error?: Error;
  onRetry?: () => void;
}

export function SlashCommandList({
  commands,
  onEdit,
  onDelete,
  onToggleEnabled,
  onCreate,
  isLoading = false,
  error,
  onRetry,
}: SlashCommandListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'date'>('date');

  const filteredCommands = useMemo(() => {
    let filtered = commands;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (cmd) =>
          cmd.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          cmd.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter === 'enabled') {
      filtered = filtered.filter((cmd) => cmd.enabled);
    } else if (statusFilter === 'disabled') {
      filtered = filtered.filter((cmd) => !cmd.enabled);
    }

    // Sort
    if (sortBy === 'name') {
      filtered = [...filtered].sort((a, b) => a.name.localeCompare(b.name));
    } else {
      filtered = [...filtered].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    }

    return filtered;
  }, [commands, searchQuery, statusFilter, sortBy]);

  if (isLoading) {
    return (
      <div role="status" aria-label="Loading slash commands">
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse bg-gray-200 h-24 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 border border-red-200 bg-red-50 rounded">
        <p className="text-red-800">Failed to load slash commands: {error.message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            aria-label="Retry loading slash commands"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (commands.length === 0 && !searchQuery) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No slash commands</h3>
        <p className="text-gray-600 mb-4">Create your first slash command to get started</p>
        {onCreate && (
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            aria-label="Create slash command"
          >
            Create Slash Command
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Header with search and create button */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1 mr-4" role="search" aria-label="Search slash commands">
          <input
            type="search"
            placeholder="Search slash commands..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Search slash commands"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
          className="px-4 py-2 border border-gray-300 rounded-lg mr-2"
          aria-label="Filter by status"
        >
          <option value="all">All Status</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </select>
        <button
          onClick={() => setSortBy(sortBy === 'name' ? 'date' : 'name')}
          className="px-4 py-2 border border-gray-300 rounded-lg mr-2"
          aria-label="Sort slash commands"
        >
          Sort by {sortBy === 'name' ? 'Date' : 'Name'}
        </button>
        {onCreate && (
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            aria-label="Create slash command"
          >
            Create Command
          </button>
        )}
      </div>

      {/* Command list */}
      {filteredCommands.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No slash commands match your search criteria
        </div>
      ) : (
        <ul role="list" aria-label="Slash commands list" className="space-y-4">
          {filteredCommands.map((command) => (
            <li
              key={command.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              role="listitem"
              tabIndex={0}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-gray-900">/{command.name}</h3>
                    <label className="flex items-center cursor-pointer" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={command.enabled}
                        onChange={(e) => onToggleEnabled(command.id, e.target.checked)}
                        className="mr-2"
                        aria-label={`Toggle ${command.name}`}
                      />
                      <span className="text-sm text-gray-600">Enabled</span>
                    </label>
                  </div>
                  <p className="text-gray-600 mt-1">{command.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`px-2 py-1 text-sm rounded ${
                      command.enabled
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {command.enabled ? 'Active' : 'Inactive'}
                    </span>
                    <span className="text-sm text-gray-500">
                      Updated {new Date(command.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onEdit(command)}
                    className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
                    aria-label={`Edit ${command.name}`}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => setDeleteConfirmId(command.id)}
                    className="px-3 py-1 text-sm text-red-600 hover:text-red-700"
                    aria-label={`Delete ${command.name}`}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Delete confirmation dialog */}
      {deleteConfirmId && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setDeleteConfirmId(null)}
        >
          <div
            className="bg-white p-6 rounded-lg max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold mb-2">Are you sure?</h3>
            <p className="text-gray-600 mb-4">
              This action cannot be undone. The slash command will be permanently deleted.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                aria-label="Cancel deletion"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onDelete(deleteConfirmId);
                  setDeleteConfirmId(null);
                }}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                aria-label="Confirm deletion"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

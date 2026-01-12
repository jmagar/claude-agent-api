'use client';

import { useState, useMemo } from 'react';
import type { AgentDefinition } from '@/types';

interface AgentListProps {
  agents: AgentDefinition[];
  onEdit: (agent: AgentDefinition) => void;
  onDelete: (id: string) => void;
  onShare: (agent: AgentDefinition) => void;
  onCreate?: () => void;
  isLoading?: boolean;
  error?: Error;
  onRetry?: () => void;
}

export function AgentList({
  agents,
  onEdit,
  onDelete,
  onShare,
  onCreate,
  isLoading = false,
  error,
  onRetry,
}: AgentListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'date'>('date');

  const filteredAgents = useMemo(() => {
    let filtered = agents;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (agent) =>
          agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          agent.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Model filter
    if (modelFilter && modelFilter !== 'all') {
      filtered = filtered.filter((agent) => agent.model === modelFilter);
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
  }, [agents, searchQuery, modelFilter, sortBy]);

  if (isLoading) {
    return (
      <div role="status" aria-label="Loading agents">
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
        <p className="text-red-800">Failed to load agents: {error.message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            aria-label="Retry loading agents"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (agents.length === 0 && !searchQuery) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No agents</h3>
        <p className="text-gray-600 mb-4">Create your first agent to get started</p>
        {onCreate && (
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            aria-label="Create agent"
          >
            Create Agent
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Header with search and create button */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1 mr-4" role="search" aria-label="Search agents">
          <input
            type="search"
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Search agents"
          />
        </div>
        <select
          value={modelFilter}
          onChange={(e) => setModelFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg mr-2"
          aria-label="Filter by model"
        >
          <option value="all">All Models</option>
          <option value="sonnet">Sonnet</option>
          <option value="opus">Opus</option>
          <option value="haiku">Haiku</option>
          <option value="inherit">Inherit</option>
        </select>
        <button
          onClick={() => setSortBy(sortBy === 'name' ? 'date' : 'name')}
          className="px-4 py-2 border border-gray-300 rounded-lg mr-2"
          aria-label="Sort agents"
        >
          Sort by {sortBy === 'name' ? 'Date' : 'Name'}
        </button>
        {onCreate && (
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            aria-label="Create agent"
          >
            Create Agent
          </button>
        )}
      </div>

      {/* Agent list */}
      {filteredAgents.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No agents match your search criteria
        </div>
      ) : (
        <ul role="list" aria-label="Agents list" className="space-y-4">
          {filteredAgents.map((agent) => (
            <li
              key={agent.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              role="listitem"
              tabIndex={0}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                  <p className="text-gray-600 mt-1">{agent.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                      {agent.model}
                    </span>
                    {agent.tools && (
                      <span className="text-sm text-gray-500">
                        {agent.tools.length} tools
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onEdit(agent)}
                    className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
                    aria-label={`Edit ${agent.name}`}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onShare(agent)}
                    className="px-3 py-1 text-sm text-green-600 hover:text-green-700"
                    aria-label={`Share ${agent.name}`}
                  >
                    Share
                  </button>
                  <button
                    onClick={() => setDeleteConfirmId(agent.id)}
                    className="px-3 py-1 text-sm text-red-600 hover:text-red-700"
                    aria-label={`Delete ${agent.name}`}
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
              This action cannot be undone. The agent will be permanently deleted.
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

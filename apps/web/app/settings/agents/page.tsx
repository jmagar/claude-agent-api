'use client';

import { useState } from 'react';
import { AgentList } from '@/components/agents/AgentList';
import { AgentForm } from '@/components/agents/AgentForm';
import { useAgents } from '@/hooks/useAgents';
import type { AgentDefinition } from '@/types';

export default function AgentsSettingsPage() {
  const {
    agents,
    isLoading,
    error,
    createAgent,
    updateAgent,
    deleteAgent,
    shareAgent,
    refetch,
  } = useAgents();

  const [isCreating, setIsCreating] = useState(false);
  const [editingAgent, setEditingAgent] = useState<AgentDefinition | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const handleCreate = () => {
    setIsCreating(true);
    setEditingAgent(null);
  };

  const handleEdit = (agent: AgentDefinition) => {
    setEditingAgent(agent);
    setIsCreating(false);
  };

  const handleSubmit = async (data: Partial<AgentDefinition>) => {
    try {
      if (editingAgent) {
        await updateAgent(editingAgent.id, data);
      } else {
        await createAgent(data);
      }
      setIsCreating(false);
      setEditingAgent(null);
    } catch (err) {
      console.error('Failed to save agent:', err);
      throw err;
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteAgent(id);
    } catch (err) {
      console.error('Failed to delete agent:', err);
    }
  };

  const handleShare = async (agent: AgentDefinition) => {
    try {
      const result = await shareAgent(agent.id);
      setShareUrl(result.share_url);
      // Auto-hide after 5 seconds
      setTimeout(() => setShareUrl(null), 5000);
    } catch (err) {
      console.error('Failed to share agent:', err);
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingAgent(null);
  };

  if (isCreating || editingAgent) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <AgentForm
          agent={editingAgent || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Agent Management</h1>
        <p className="text-gray-600 mt-2">
          Create and manage AI agents with custom prompts and tools
        </p>
      </div>

      {shareUrl && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 font-medium">Share URL generated!</p>
          <div className="mt-2 flex items-center gap-2">
            <input
              type="text"
              value={shareUrl}
              readOnly
              className="flex-1 px-3 py-2 border border-green-300 rounded bg-white"
            />
            <button
              onClick={() => {
                navigator.clipboard.writeText(shareUrl);
              }}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Copy
            </button>
          </div>
        </div>
      )}

      <AgentList
        agents={agents}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onShare={handleShare}
        onCreate={handleCreate}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
      />
    </div>
  );
}

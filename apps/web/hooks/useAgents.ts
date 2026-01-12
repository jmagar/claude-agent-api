/**
 * useAgents Hook
 *
 * React Query hook for managing agent data with CRUD operations.
 *
 * Features:
 * - Fetch all agents
 * - Create new agent
 * - Update existing agent
 * - Delete agent
 * - Share agent (generate share URL)
 * - Automatic cache invalidation
 * - Optimistic updates
 *
 * @example
 * ```tsx
 * const { agents, isLoading, createAgent, updateAgent, deleteAgent } = useAgents();
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AgentDefinition } from '@/types';

/**
 * API base URL
 */
const API_BASE_URL = '/api/agents';

/**
 * Fetch all agents
 */
async function fetchAgents(): Promise<AgentDefinition[]> {
  const response = await fetch(API_BASE_URL);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to fetch agents');
  }

  const data = await response.json();
  return data.agents || [];
}

/**
 * Create a new agent
 */
async function createAgent(data: Partial<AgentDefinition>): Promise<AgentDefinition> {
  const response = await fetch(API_BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to create agent');
  }

  const result = await response.json();
  return result.agent;
}

/**
 * Update an existing agent
 */
async function updateAgent({
  id,
  data,
}: {
  id: string;
  data: Partial<AgentDefinition>;
}): Promise<AgentDefinition> {
  const response = await fetch(`${API_BASE_URL}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to update agent');
  }

  const result = await response.json();
  return result.agent;
}

/**
 * Delete an agent
 */
async function deleteAgent(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to delete agent');
  }
}

/**
 * Share an agent (generate public share URL)
 */
async function shareAgent(id: string): Promise<{ share_url: string }> {
  const response = await fetch(`${API_BASE_URL}/${id}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to share agent');
  }

  return response.json();
}

/**
 * useAgents Hook
 */
export function useAgents() {
  const queryClient = useQueryClient();

  // Fetch agents query
  const {
    data: agents = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  // Create agent mutation
  const createMutation = useMutation({
    mutationFn: createAgent,
    onSuccess: () => {
      // Invalidate and refetch agents list
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Update agent mutation
  const updateMutation = useMutation({
    mutationFn: updateAgent,
    onSuccess: () => {
      // Invalidate and refetch agents list
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Delete agent mutation
  const deleteMutation = useMutation({
    mutationFn: deleteAgent,
    onSuccess: () => {
      // Invalidate and refetch agents list
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Share agent mutation
  const shareMutation = useMutation({
    mutationFn: shareAgent,
    onSuccess: () => {
      // Invalidate and refetch agents list (to update is_shared status)
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  return {
    // Data
    agents,
    isLoading,
    error: error as Error | undefined,

    // Actions
    createAgent: createMutation.mutateAsync,
    updateAgent: (id: string, data: Partial<AgentDefinition>) =>
      updateMutation.mutateAsync({ id, data }),
    deleteAgent: deleteMutation.mutateAsync,
    shareAgent: shareMutation.mutateAsync,
    refetch,

    // Mutation states
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isSharing: shareMutation.isPending,

    // Mutation errors
    createError: createMutation.error as Error | undefined,
    updateError: updateMutation.error as Error | undefined,
    deleteError: deleteMutation.error as Error | undefined,
    shareError: shareMutation.error as Error | undefined,
  };
}

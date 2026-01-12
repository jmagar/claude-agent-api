/**
 * useAgents Hook
 *
 * React Query hook for managing agent data with CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import type { AgentDefinition } from '@/types';
import { queryKeys } from '@/lib/query-keys';
import { createOptimisticHandlers } from '@/lib/react-query/optimistic';

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
  return data.agents || data || [];
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
  return result.agent ?? result;
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
  return result.agent ?? result;
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
async function shareAgent(id: string): Promise<{ share_url: string; share_token?: string }> {
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
  const queryKey = queryKeys.agents.lists();

  // Fetch agents query
  const {
    data: agents = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: fetchAgents,
  });

  // Create agent mutation
  const createMutation = useMutation({
    mutationFn: createAgent,
    ...createOptimisticHandlers<AgentDefinition[], Partial<AgentDefinition>>({
      queryClient,
      queryKey,
      updater: (current, variables) => {
        const now = new Date().toISOString();
        const optimistic: AgentDefinition = {
          id: uuidv4(),
          name: variables.name ?? 'New Agent',
          description: variables.description ?? '',
          prompt: variables.prompt ?? '',
          tools: variables.tools,
          model: variables.model,
          created_at: now,
          updated_at: now,
          is_shared: false,
        };

        return [optimistic, ...(current ?? [])];
      },
    }),
  });

  // Update agent mutation
  const updateMutation = useMutation({
    mutationFn: updateAgent,
    ...createOptimisticHandlers<AgentDefinition[], { id: string; data: Partial<AgentDefinition> }>({
      queryClient,
      queryKey,
      updater: (current, variables) =>
        (current ?? []).map((agent) =>
          agent.id === variables.id
            ? {
                ...agent,
                ...variables.data,
                updated_at: new Date().toISOString(),
              }
            : agent
        ),
    }),
  });

  // Delete agent mutation
  const deleteMutation = useMutation({
    mutationFn: deleteAgent,
    ...createOptimisticHandlers<AgentDefinition[], string>({
      queryClient,
      queryKey,
      updater: (current, id) => (current ?? []).filter((agent) => agent.id !== id),
    }),
  });

  // Share agent mutation
  const shareMutation = useMutation({
    mutationFn: shareAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
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

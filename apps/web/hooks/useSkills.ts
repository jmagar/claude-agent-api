/**
 * useSkills Hook
 *
 * React Query hook for managing skill data with CRUD operations.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import type { SkillDefinition } from '@/types';
import { queryKeys } from '@/lib/query-keys';
import { createOptimisticHandlers } from '@/lib/react-query/optimistic';

/**
 * API base URL
 */
const API_BASE_URL = '/api/skills';

/**
 * Fetch all skills
 */
async function fetchSkills(): Promise<SkillDefinition[]> {
  const response = await fetch(API_BASE_URL);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to fetch skills');
  }

  const data = await response.json();
  return data.skills || data || [];
}

/**
 * Create a new skill
 */
async function createSkill(data: Partial<SkillDefinition>): Promise<SkillDefinition> {
  const response = await fetch(API_BASE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to create skill');
  }

  const result = await response.json();
  return result.skill ?? result;
}

/**
 * Update an existing skill
 */
async function updateSkill({
  id,
  data,
}: {
  id: string;
  data: Partial<SkillDefinition>;
}): Promise<SkillDefinition> {
  const response = await fetch(`${API_BASE_URL}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to update skill');
  }

  const result = await response.json();
  return result.skill ?? result;
}

/**
 * Delete a skill
 */
async function deleteSkill(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to delete skill');
  }
}

/**
 * Share a skill (generate public share URL)
 */
async function shareSkill(id: string): Promise<{ share_url: string; share_token?: string }> {
  const response = await fetch(`${API_BASE_URL}/${id}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to share skill');
  }

  return response.json();
}

/**
 * useSkills Hook
 */
export function useSkills() {
  const queryClient = useQueryClient();
  const queryKey = queryKeys.skills.lists();

  // Fetch skills query
  const {
    data: skills = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey,
    queryFn: fetchSkills,
  });

  // Create skill mutation
  const createMutation = useMutation({
    mutationFn: createSkill,
    ...createOptimisticHandlers<SkillDefinition[], Partial<SkillDefinition>>({
      queryClient,
      queryKey,
      updater: (current, variables) => {
        const now = new Date().toISOString();
        const optimistic: SkillDefinition = {
          id: uuidv4(),
          name: variables.name ?? 'New Skill',
          description: variables.description ?? '',
          content: variables.content ?? '',
          enabled: variables.enabled ?? true,
          created_at: now,
          updated_at: now,
          is_shared: false,
        };

        return [optimistic, ...(current ?? [])];
      },
    }),
  });

  // Update skill mutation
  const updateMutation = useMutation({
    mutationFn: updateSkill,
    ...createOptimisticHandlers<SkillDefinition[], { id: string; data: Partial<SkillDefinition> }>({
      queryClient,
      queryKey,
      updater: (current, variables) =>
        (current ?? []).map((skill) =>
          skill.id === variables.id
            ? {
                ...skill,
                ...variables.data,
                updated_at: new Date().toISOString(),
              }
            : skill
        ),
    }),
  });

  // Delete skill mutation
  const deleteMutation = useMutation({
    mutationFn: deleteSkill,
    ...createOptimisticHandlers<SkillDefinition[], string>({
      queryClient,
      queryKey,
      updater: (current, id) => (current ?? []).filter((skill) => skill.id !== id),
    }),
  });

  // Share skill mutation
  const shareMutation = useMutation({
    mutationFn: shareSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  return {
    // Data
    skills,
    isLoading,
    error: error as Error | undefined,

    // Actions
    createSkill: createMutation.mutateAsync,
    updateSkill: (id: string, data: Partial<SkillDefinition>) =>
      updateMutation.mutateAsync({ id, data }),
    deleteSkill: deleteMutation.mutateAsync,
    shareSkill: shareMutation.mutateAsync,
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

/**
 * useSkills Hook
 *
 * React Query hook for managing skill data with CRUD operations.
 *
 * Features:
 * - Fetch all skills
 * - Create new skill
 * - Update existing skill
 * - Delete skill
 * - Share skill (generate share URL)
 * - Automatic cache invalidation
 * - Optimistic updates
 *
 * @example
 * ```tsx
 * const { skills, isLoading, createSkill, updateSkill, deleteSkill } = useSkills();
 * ```
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { SkillDefinition } from '@/types';

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
  return data.skills || [];
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
  return result.skill;
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
  return result.skill;
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
async function shareSkill(id: string): Promise<{ share_url: string }> {
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

  // Fetch skills query
  const {
    data: skills = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['skills'],
    queryFn: fetchSkills,
  });

  // Create skill mutation
  const createMutation = useMutation({
    mutationFn: createSkill,
    onSuccess: () => {
      // Invalidate and refetch skills list
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  // Update skill mutation
  const updateMutation = useMutation({
    mutationFn: updateSkill,
    onSuccess: () => {
      // Invalidate and refetch skills list
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  // Delete skill mutation
  const deleteMutation = useMutation({
    mutationFn: deleteSkill,
    onSuccess: () => {
      // Invalidate and refetch skills list
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });

  // Share skill mutation
  const shareMutation = useMutation({
    mutationFn: shareSkill,
    onSuccess: () => {
      // Invalidate and refetch skills list (to update is_shared status)
      queryClient.invalidateQueries({ queryKey: ['skills'] });
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

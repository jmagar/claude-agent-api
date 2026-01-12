'use client';

import { useState } from 'react';
import { SkillList } from '@/components/skills/SkillList';
import { SkillEditor } from '@/components/skills/SkillEditor';
import { useSkills } from '@/hooks/useSkills';
import type { SkillDefinition } from '@/types';

export default function SkillsSettingsPage() {
  const {
    skills,
    isLoading,
    error,
    createSkill,
    updateSkill,
    deleteSkill,
    shareSkill,
    refetch,
  } = useSkills();

  const [isCreating, setIsCreating] = useState(false);
  const [editingSkill, setEditingSkill] = useState<SkillDefinition | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);

  const handleCreate = () => {
    setIsCreating(true);
    setEditingSkill(null);
  };

  const handleEdit = (skill: SkillDefinition) => {
    setEditingSkill(skill);
    setIsCreating(false);
  };

  const handleSubmit = async (data: Partial<SkillDefinition>) => {
    try {
      if (editingSkill) {
        await updateSkill(editingSkill.id, data);
      } else {
        await createSkill(data);
      }
      setIsCreating(false);
      setEditingSkill(null);
    } catch (err) {
      console.error('Failed to save skill:', err);
      throw err;
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteSkill(id);
    } catch (err) {
      console.error('Failed to delete skill:', err);
    }
  };

  const handleShare = async (skill: SkillDefinition) => {
    try {
      const result = await shareSkill(skill.id);
      setShareUrl(result.share_url);
      setTimeout(() => setShareUrl(null), 5000);
    } catch (err) {
      console.error('Failed to share skill:', err);
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingSkill(null);
  };

  if (isCreating || editingSkill) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <SkillEditor
          skill={editingSkill || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          onShare={editingSkill ? () => handleShare(editingSkill) : undefined}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Skill Management</h1>
        <p className="text-gray-600 mt-2">
          Create and manage reusable skills for AI agents
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

      <SkillList
        skills={skills}
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

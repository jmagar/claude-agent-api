'use client';

import { useState, useMemo } from 'react';
import type { SkillDefinition } from '@/types';

interface SkillListProps {
  skills: SkillDefinition[];
  onEdit: (skill: SkillDefinition) => void;
  onDelete: (id: string) => void;
  onShare: (skill: SkillDefinition) => void;
  onCreate?: () => void;
  isLoading?: boolean;
  error?: Error;
  onRetry?: () => void;
}

export function SkillList({
  skills,
  onEdit,
  onDelete,
  onShare,
  onCreate,
  isLoading = false,
  error,
  onRetry,
}: SkillListProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'date'>('date');

  const filteredSkills = useMemo(() => {
    let filtered = skills;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (skill) =>
          skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          skill.description.toLowerCase().includes(searchQuery.toLowerCase())
      );
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
  }, [skills, searchQuery, sortBy]);

  if (isLoading) {
    return (
      <div role="status" aria-label="Loading skills">
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
        <p className="text-red-800">Failed to load skills: {error.message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            aria-label="Retry loading skills"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (skills.length === 0 && !searchQuery) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No skills</h3>
        <p className="text-gray-600 mb-4">Create your first skill to get started</p>
        {onCreate && (
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            aria-label="Create skill"
          >
            Create Skill
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      {/* Header with search and create button */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex-1 mr-4" role="search" aria-label="Search skills">
          <input
            type="search"
            placeholder="Search skills..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Search skills"
          />
        </div>
        <button
          onClick={() => setSortBy(sortBy === 'name' ? 'date' : 'name')}
          className="px-4 py-2 border border-gray-300 rounded-lg mr-2"
          aria-label="Sort skills"
        >
          Sort by {sortBy === 'name' ? 'Date' : 'Name'}
        </button>
        {onCreate && (
          <button
            onClick={onCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            aria-label="Create skill"
          >
            Create Skill
          </button>
        )}
      </div>

      {/* Skill list */}
      {filteredSkills.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No skills match your search criteria
        </div>
      ) : (
        <ul role="list" aria-label="Skills list" className="space-y-4">
          {filteredSkills.map((skill) => (
            <li
              key={skill.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              role="listitem"
              tabIndex={0}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{skill.name}</h3>
                  <p className="text-gray-600 mt-1">{skill.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    {skill.is_shared && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded">
                        Shared
                      </span>
                    )}
                    <span className="text-sm text-gray-500">
                      Updated {new Date(skill.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => onEdit(skill)}
                    className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
                    aria-label={`Edit ${skill.name}`}
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onShare(skill)}
                    className="px-3 py-1 text-sm text-green-600 hover:text-green-700"
                    aria-label={`Share ${skill.name}`}
                  >
                    Share
                  </button>
                  <button
                    onClick={() => setDeleteConfirmId(skill.id)}
                    className="px-3 py-1 text-sm text-red-600 hover:text-red-700"
                    aria-label={`Delete ${skill.name}`}
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
              This action cannot be undone. The skill will be permanently deleted.
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

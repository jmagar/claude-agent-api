'use client';

import { useState, FormEvent } from 'react';
import type { SkillDefinition } from '@/types';

interface SkillEditorProps {
  skill?: SkillDefinition;
  onSubmit: (data: Partial<SkillDefinition>) => void | Promise<void>;
  onCancel: () => void;
  onShare?: (skill: SkillDefinition) => void;
}

export function SkillEditor({ skill, onSubmit, onCancel, onShare }: SkillEditorProps) {
  const [name, setName] = useState(skill?.name || '');
  const [description, setDescription] = useState(skill?.description || '');
  const [content, setContent] = useState(skill?.content || '');
  const [enabled, setEnabled] = useState(skill?.enabled ?? true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [viewMode, setViewMode] = useState<'visual' | 'yaml' | 'preview'>('visual');
  const [yamlError, setYamlError] = useState<string>('');

  const validateName = (value: string) => {
    if (!value.trim()) {
      return 'Name is required';
    } else if (!/^[a-z0-9-]+$/.test(value)) {
      return 'Name must be kebab-case (lowercase letters, numbers, and hyphens only)';
    }
    return '';
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    const nameError = validateName(name);
    if (nameError) newErrors.name = nameError;

    if (!description.trim()) {
      newErrors.description = 'Description is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Combine frontmatter with content
      const fullContent = `---
name: ${name}
description: ${description}
---

${content}`;

      await onSubmit({
        name,
        description,
        content: fullContent,
        enabled,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Simple markdown to HTML converter for preview
  const renderPreview = () => {
    // Extract markdown content (remove frontmatter)
    const markdownContent = content.replace(/^---[\s\S]*?---\n/, '');

    // Basic markdown rendering
    const html = markdownContent
      .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mb-4">$1</h1>')
      .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mb-3">$1</h2>')
      .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mb-2">$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded">$1</code>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul class="list-disc pl-6 mb-4">$1</ul>')
      .replace(/\n\n/g, '<br /><br />');

    return <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Skill editor" className="space-y-6 max-w-2xl">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">{skill ? 'Edit Skill' : 'Create Skill'}</h2>
        {skill && onShare && (
          <button
            type="button"
            onClick={() => onShare(skill)}
            className="px-4 py-2 text-blue-600 hover:text-blue-700"
            aria-label="Share skill"
          >
            Share
          </button>
        )}
      </div>

      {/* Name field */}
      <div>
        <label htmlFor="skill-name" className="block text-sm font-medium text-gray-700 mb-1">
          Name
        </label>
        <input
          id="skill-name"
          type="text"
          value={name}
          onChange={(e) => {
            const value = e.target.value;
            setName(value);
            const error = validateName(value);
            setErrors(prev => ({ ...prev, name: error }));
          }}
          required
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="my-skill"
        />
        {errors.name && (
          <p role="alert" className="text-sm text-red-600 mt-1">
            {errors.name}
          </p>
        )}
      </div>

      {/* Description field */}
      <div>
        <label htmlFor="skill-description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="skill-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe what this skill does..."
        />
        {errors.description && (
          <p role="alert" className="text-sm text-red-600 mt-1">
            {errors.description}
          </p>
        )}
      </div>

      {/* Enabled toggle */}
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="skill-enabled"
          role="switch"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="w-10 h-6 rounded-full relative cursor-pointer"
          aria-label="Enabled"
        />
        <label htmlFor="skill-enabled" className="text-sm font-medium text-gray-700">
          Enabled
        </label>
      </div>

      {/* Content editor with tabs */}
      <div>
        <div className="flex border-b border-gray-200 mb-4">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'visual'}
            onClick={() => setViewMode('visual')}
            className={`px-4 py-2 ${
              viewMode === 'visual'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Edit
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'yaml'}
            onClick={() => setViewMode('yaml')}
            className={`px-4 py-2 ${
              viewMode === 'yaml'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            aria-label="YAML view"
          >
            YAML View
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === 'preview'}
            onClick={() => setViewMode('preview')}
            className={`px-4 py-2 ${
              viewMode === 'preview'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Preview
          </button>
        </div>

        {viewMode === 'visual' && (
          <div>
            <label htmlFor="skill-content" className="block text-sm font-medium text-gray-700 mb-1">
              Content
            </label>
            <textarea
              id="skill-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={15}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="# Skill Content\n\nWrite your skill documentation in Markdown..."
              aria-label="Content editor"
            />
            {/* Toolbar */}
            <div className="flex gap-2 mt-2">
              <button
                type="button"
                className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
                aria-label="Bold"
              >
                <strong>B</strong>
              </button>
              <button
                type="button"
                className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
                aria-label="Italic"
              >
                <em>I</em>
              </button>
              <button
                type="button"
                className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
                aria-label="Heading"
              >
                H
              </button>
              <button
                type="button"
                className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50"
                aria-label="Code block"
              >
                {'</>'}
              </button>
            </div>
          </div>
        )}

        {viewMode === 'yaml' && (
          <div>
            <label htmlFor="skill-yaml" className="block text-sm font-medium text-gray-700 mb-1">
              YAML Frontmatter + Content
            </label>
            <textarea
              id="skill-yaml"
              value={`---\nname: ${name}\ndescription: ${description}\n---\n${content}`}
              onChange={(e) => {
                const fullContent = e.target.value;

                // Basic YAML validation
                const lines = fullContent.split('\n');
                const delimiterCount = lines.filter(line => line.trim() === '---').length;

                if (delimiterCount < 2) {
                  setYamlError('Invalid YAML: Missing frontmatter delimiters');
                } else if (fullContent.includes(': :')) {
                  setYamlError('Invalid YAML: Syntax error detected');
                } else {
                  setYamlError('');
                  // Simple parsing (would use proper YAML parser in production)
                  const parts = fullContent.split('---\n');
                  if (parts.length >= 3) {
                    setContent(parts.slice(2).join('---\n'));
                  }
                }
              }}
              rows={20}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              aria-label="YAML editor"
            />
            {yamlError && (
              <p role="alert" className="text-sm text-red-600 mt-1">
                {yamlError}
              </p>
            )}
          </div>
        )}

        {viewMode === 'preview' && (
          <div className="border border-gray-300 rounded-lg p-6 min-h-96">
            <h2 className="text-2xl font-bold mb-4">{name || 'Untitled Skill'}</h2>
            <p className="text-gray-600 mb-6">{description || 'No description'}</p>
            <div className="border-t border-gray-200 pt-6">{renderPreview()}</div>
          </div>
        )}
      </div>

      {/* Form actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={isSubmitting}
          aria-label="Save skill"
        >
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  );
}

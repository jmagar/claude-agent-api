'use client';

import { useState, FormEvent } from 'react';
import Markdown from 'react-markdown';
import { PlateMarkdownEditor } from '@/components/plate';
import type { SlashCommand } from '@/types';

interface SlashCommandEditorProps {
  command?: SlashCommand;
  onSubmit: (data: Partial<SlashCommand>) => void | Promise<void>;
  onCancel: () => void;
}

export function SlashCommandEditor({ command, onSubmit, onCancel }: SlashCommandEditorProps) {
  const [name, setName] = useState(command?.name || '');
  const [description, setDescription] = useState(command?.description || '');
  const [content, setContent] = useState(command?.content || '');
  const [enabled, setEnabled] = useState(command?.enabled ?? true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [viewMode, setViewMode] = useState<'visual' | 'yaml' | 'preview'>('visual');
  const [yamlError, setYamlError] = useState<string>('');

  const validateName = (value: string) => {
    if (!value.trim()) {
      return 'Name is required';
    } else if (!/^[a-z0-9-]+$/.test(value)) {
      return 'Name must be kebab-case (lowercase letters, numbers, and hyphens only)';
    } else if (value.length > 50) {
      return 'Name must be 50 characters or less';
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

    if (!content.trim()) {
      newErrors.content = 'Content is required';
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
      await onSubmit({
        name,
        description,
        content,
        enabled,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Extract markdown content (remove frontmatter) for preview
  const getMarkdownContent = () => {
    return content.replace(/^---[\s\S]*?---\n/, '');
  };

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Slash command editor" className="space-y-6 max-w-2xl">
      <h2 className="text-2xl font-bold">{command ? 'Edit Slash Command' : 'Create Slash Command'}</h2>

      {/* Name field */}
      <div>
        <label htmlFor="command-name" className="block text-sm font-medium text-gray-700 mb-1">
          Command Name (without /)
        </label>
        <div className="flex items-center">
          <span className="text-2xl text-gray-500 mr-2">/</span>
          <input
            id="command-name"
            type="text"
            value={name}
            onChange={(e) => {
              const value = e.target.value;
              setName(value);
              const error = validateName(value);
              setErrors(prev => ({ ...prev, name: error }));
            }}
            required
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="my-command"
          />
        </div>
        {errors.name && (
          <p role="alert" className="text-sm text-red-600 mt-1">
            {errors.name}
          </p>
        )}
      </div>

      {/* Description field */}
      <div>
        <label htmlFor="command-description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="command-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={2}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe what this command does..."
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
          id="command-enabled"
          role="switch"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="w-10 h-6 rounded-full relative cursor-pointer"
          aria-label="Enabled"
        />
        <label htmlFor="command-enabled" className="text-sm font-medium text-gray-700">
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
            <label htmlFor="command-content" className="block text-sm font-medium text-gray-700 mb-1">
              Content
            </label>
            <PlateMarkdownEditor
              value={content}
              onChange={setContent}
              placeholder="# Command Instructions\n\nWrite your command instructions in Markdown..."
              ariaLabel="Content editor"
              showYamlTab={false}
              showPreviewTab={false}
            />
            {errors.content && (
              <p role="alert" className="text-sm text-red-600 mt-1">
                {errors.content}
              </p>
            )}
          </div>
        )}

        {viewMode === 'yaml' && (
          <div>
            <label htmlFor="command-yaml" className="block text-sm font-medium text-gray-700 mb-1">
              YAML Frontmatter + Content
            </label>
            <textarea
              id="command-yaml"
              value={`---\nname: ${name}\ndescription: ${description}\nenabled: ${enabled}\n---\n${content}`}
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
              rows={15}
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
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl text-gray-600">/</span>
              <h2 className="text-2xl font-bold">{name || 'Untitled Command'}</h2>
            </div>
            <p className="text-gray-600 mb-6">{description || 'No description'}</p>
            <div className="border-t border-gray-200 pt-6 prose max-w-none">
              <Markdown>
                {getMarkdownContent()}
              </Markdown>
            </div>
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
          aria-label="Save slash command"
        >
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  );
}

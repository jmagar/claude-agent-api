'use client';

import { useState, FormEvent } from 'react';
import type { AgentDefinition } from '@/types';

interface AgentFormProps {
  agent?: AgentDefinition;
  onSubmit: (data: Partial<AgentDefinition>) => void | Promise<void>;
  onCancel: () => void;
}

export function AgentForm({ agent, onSubmit, onCancel }: AgentFormProps) {
  const [name, setName] = useState(agent?.name || '');
  const [description, setDescription] = useState(agent?.description || '');
  const [prompt, setPrompt] = useState(agent?.prompt || '');
  const [model, setModel] = useState<'sonnet' | 'opus' | 'haiku' | 'inherit'>(
    agent?.model || 'inherit'
  );
  const [selectedTools, setSelectedTools] = useState<string[]>(agent?.tools || []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showToolsMenu, setShowToolsMenu] = useState(false);
  const [viewMode, setViewMode] = useState<'visual' | 'yaml'>('visual');
  const [yamlError, setYamlError] = useState<string>('');

  const availableTools = [
    'Read',
    'Write',
    'Edit',
    'Bash',
    'Grep',
    'Glob',
    'Task',
    'WebFetch',
    'WebSearch',
  ];

  const validateName = (value: string) => {
    if (!value.trim()) {
      return 'Name is required';
    } else if (!/^[a-z0-9-]+$/.test(value)) {
      return 'Name must be kebab-case (lowercase letters, numbers, and hyphens only)';
    } else if (value.length > 100) {
      return 'Name must be 100 characters or less';
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

    if (!prompt.trim()) {
      newErrors.prompt = 'Prompt is required';
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
        prompt,
        model,
        tools: selectedTools,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleTool = (tool: string) => {
    setSelectedTools((prev) =>
      prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool]
    );
  };

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Agent form" className="space-y-6 max-w-2xl">
      <h2 className="text-2xl font-bold">{agent ? 'Edit Agent' : 'Create Agent'}</h2>

      {/* Name field */}
      <div>
        <label htmlFor="agent-name" className="block text-sm font-medium text-gray-700 mb-1">
          Name
        </label>
        <input
          id="agent-name"
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
          placeholder="my-agent"
        />
        {errors.name && (
          <p role="alert" className="text-sm text-red-600 mt-1">
            {errors.name}
          </p>
        )}
      </div>

      {/* Description field */}
      <div>
        <label htmlFor="agent-description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          id="agent-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
          rows={3}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe what this agent does..."
        />
        {errors.description && (
          <p role="alert" className="text-sm text-red-600 mt-1">
            {errors.description}
          </p>
        )}
      </div>

      {/* Model selector */}
      <div>
        <label htmlFor="agent-model" className="block text-sm font-medium text-gray-700 mb-1">
          Model
        </label>
        <select
          id="agent-model"
          value={model}
          onChange={(e) => setModel(e.target.value as typeof model)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="inherit">Inherit</option>
          <option value="sonnet">Sonnet</option>
          <option value="opus">Opus</option>
          <option value="haiku">Haiku</option>
        </select>
      </div>

      {/* Prompt editor with view toggle */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <label htmlFor="agent-prompt" className="block text-sm font-medium text-gray-700">
            Prompt
          </label>
          <button
            type="button"
            onClick={() => setViewMode(viewMode === 'visual' ? 'yaml' : 'visual')}
            className="text-sm text-blue-600 hover:text-blue-700"
            aria-label="Toggle YAML view"
          >
            {viewMode === 'visual' ? 'YAML View' : 'Visual View'}
          </button>
        </div>

        {viewMode === 'visual' ? (
          <div>
            <textarea
              id="agent-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
              rows={10}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="You are a helpful AI agent..."
              aria-label="Prompt editor"
            />
            {/* Toolbar for basic formatting */}
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
        ) : (
          <div>
            <textarea
              id="agent-prompt-yaml"
              value={`---\nname: ${name}\ndescription: ${description}\nmodel: ${model}\n---\n${prompt}`}
              onChange={(e) => {
                const content = e.target.value;

                // Basic YAML validation
                const lines = content.split('\n');
                const delimiterCount = lines.filter(line => line.trim() === '---').length;

                if (delimiterCount < 2) {
                  setYamlError('Invalid YAML: Missing frontmatter delimiters');
                } else if (content.includes(': :')) {
                  setYamlError('Invalid YAML: Syntax error detected');
                } else {
                  setYamlError('');
                  setPrompt(content.split('---\n').slice(2).join('---\n'));
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

        {errors.prompt && (
          <p role="alert" className="text-sm text-red-600 mt-1">
            {errors.prompt}
          </p>
        )}
      </div>

      {/* Tools selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Allowed Tools</label>
        <button
          type="button"
          onClick={() => setShowToolsMenu(!showToolsMenu)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-left focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Select tools"
        >
          {selectedTools.length === 0
            ? 'Select tools...'
            : `${selectedTools.length} tools selected`}
        </button>

        {showToolsMenu && (
          <div className="mt-2 border border-gray-300 rounded-lg p-4 space-y-2">
            {availableTools.map((tool) => (
              <label key={tool} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedTools.includes(tool)}
                  onChange={() => toggleTool(tool)}
                  className="rounded border-gray-300"
                  aria-label={`Select ${tool} tool`}
                />
                <span>{tool}</span>
              </label>
            ))}
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
          aria-label="Save agent"
        >
          {isSubmitting ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  );
}

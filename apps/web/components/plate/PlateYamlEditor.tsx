/**
 * PlateYamlEditor Component
 *
 * YAML-aware editor for agent prompts with dual-mode editing (Visual/YAML).
 * Integrates PlateEditor for content body and textarea for full YAML view.
 */

'use client';

import * as React from 'react';
import { PlateEditor } from './PlateEditor';
import { useYamlFrontmatter } from './hooks/useYamlFrontmatter';
import { useMarkdownSync } from './hooks/useMarkdownSync';
import { validateYamlFrontmatter } from '@/lib/yaml-validation';

export interface PlateYamlEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel?: string;
  validateYaml?: boolean;
  requiredFields?: string[];
}

type TabMode = 'visual' | 'yaml';

/**
 * PlateYamlEditor - YAML-aware editor with Visual/YAML toggle
 *
 * Provides two editing modes:
 * - Visual: Rich text editor (PlateJS) for content body only
 * - YAML: Raw markdown textarea with frontmatter + content
 *
 * @param props - PlateYamlEditorProps
 * @returns React component
 */
export function PlateYamlEditor({
  value,
  onChange,
  placeholder = 'Start writing...',
  ariaLabel = 'YAML editor',
  validateYaml = false,
  requiredFields = [],
}: PlateYamlEditorProps) {
  const [activeTab, setActiveTab] = React.useState<TabMode>('visual');

  // Use YAML frontmatter hook to manage frontmatter and body separately
  const { body, updateBody } = useYamlFrontmatter(value, onChange);

  // Use markdown sync for PlateJS editor (body only)
  const { slateValue, handleSlateChange } = useMarkdownSync(body, updateBody);

  // Handle raw YAML changes
  const handleRawYamlChange = React.useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value);
    },
    [onChange]
  );

  // Validate YAML if enabled
  const validation = React.useMemo(() => {
    if (!validateYaml) {
      return { isValid: true, errors: [], warnings: [], data: {} };
    }
    return validateYamlFrontmatter(value, requiredFields);
  }, [validateYaml, value, requiredFields]);

  return (
    <div className="space-y-4" aria-label={ariaLabel}>
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'visual'}
          onClick={() => setActiveTab('visual')}
          className={`px-4 py-2 ${
            activeTab === 'visual'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Visual
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'yaml'}
          onClick={() => setActiveTab('yaml')}
          className={`px-4 py-2 ${
            activeTab === 'yaml'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
          aria-label="YAML view"
        >
          YAML
        </button>
      </div>

      {/* Tab Content */}
      <div role="tabpanel">
        {activeTab === 'visual' && (
          <div className="space-y-2">
            <PlateEditor
              value={slateValue}
              onChange={handleSlateChange}
              placeholder={placeholder}
              ariaLabel={ariaLabel}
              minHeight="300px"
            />
          </div>
        )}

        {activeTab === 'yaml' && (
          <div>
            <textarea
              value={value}
              onChange={handleRawYamlChange}
              rows={20}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              placeholder="YAML frontmatter + content..."
              aria-label="YAML editor"
            />
            {!validation.isValid && (
              <div role="alert" className="text-sm text-red-600 mt-2">
                {validation.errors.map((error, index) => (
                  <p key={index}>{error}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

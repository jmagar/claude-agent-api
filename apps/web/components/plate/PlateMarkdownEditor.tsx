/**
 * PlateMarkdownEditor Component
 *
 * Complete markdown editor with tabs (Edit/YAML/Preview) for Skills and Commands.
 * Integrates PlateEditor + PlateMarkdownToolbar for rich text editing.
 */

'use client';

import * as React from 'react';
import Markdown from 'react-markdown';
import { PlateEditor } from './PlateEditor';
import { PlateMarkdownToolbar } from './PlateMarkdownToolbar';
import { useMarkdownSync } from './hooks/useMarkdownSync';

export interface PlateMarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  ariaLabel?: string;
  showYamlTab?: boolean;
  showPreviewTab?: boolean;
}

type TabMode = 'edit' | 'yaml' | 'preview';

/**
 * PlateMarkdownEditor - Complete markdown editor with tabs
 *
 * Provides three editing modes:
 * - Edit: Rich text editor (PlateJS)
 * - YAML View: Raw markdown textarea
 * - Preview: Rendered markdown
 *
 * @param props - PlateMarkdownEditorProps
 * @returns React component
 */
export function PlateMarkdownEditor({
  value,
  onChange,
  placeholder = 'Start writing...',
  ariaLabel = 'Markdown editor',
  showYamlTab = true,
  showPreviewTab = true,
}: PlateMarkdownEditorProps) {
  const [activeTab, setActiveTab] = React.useState<TabMode>('edit');
  const { slateValue, handleSlateChange } = useMarkdownSync(value, onChange);

  // Handle raw markdown changes in YAML view
  const handleRawMarkdownChange = React.useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value);
    },
    [onChange]
  );

  return (
    <div className="space-y-4" aria-label={ariaLabel}>
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'edit'}
          onClick={() => setActiveTab('edit')}
          className={`px-4 py-2 ${
            activeTab === 'edit'
              ? 'border-b-2 border-blue-600 text-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Edit
        </button>

        {showYamlTab && (
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
            YAML View
          </button>
        )}

        {showPreviewTab && (
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'preview'}
            onClick={() => setActiveTab('preview')}
            className={`px-4 py-2 ${
              activeTab === 'preview'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Preview
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div role="tabpanel">
        {activeTab === 'edit' && (
          <div className="space-y-2">
            <PlateMarkdownToolbar />
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
          <textarea
            value={value}
            onChange={handleRawMarkdownChange}
            rows={20}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            placeholder="Raw markdown content..."
            aria-label="Raw markdown editor"
          />
        )}

        {activeTab === 'preview' && (
          <div className="border border-gray-300 rounded-lg p-6 min-h-[300px] prose max-w-none">
            <Markdown>
              {value || '*No content to preview*'}
            </Markdown>
          </div>
        )}
      </div>
    </div>
  );
}

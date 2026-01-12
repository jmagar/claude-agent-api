'use client';

import { useCallback, useMemo } from 'react';
import { Plate, PlateContent, createPlugins } from '@udecode/plate-core/react';
import { createParagraphPlugin } from '@udecode/plate-paragraph';
import { createHeadingPlugin } from '@udecode/plate-heading';
import { createBasicMarksPlugin } from '@udecode/plate-basic-marks';
import { createListPlugin } from '@udecode/plate-list';
import { createCodeBlockPlugin } from '@udecode/plate-code-block';
import { createBlockquotePlugin } from '@udecode/plate-block-quote';
import { createLinkPlugin } from '@udecode/plate-link';
import { createHorizontalRulePlugin } from '@udecode/plate-horizontal-rule';
import { createAutoformatPlugin } from '@udecode/plate-autoformat';
import type { SlateValue } from '@/lib/slate-serializers';

export interface PlateEditorProps {
  value: SlateValue;
  onChange: (value: SlateValue) => void;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  autoFocus?: boolean;
  minHeight?: string;
  maxHeight?: string;
  id?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
}

/**
 * PlateEditor Component
 *
 * A rich text editor built on PlateJS with markdown support.
 * Uses pre-installed @udecode packages for plugin functionality.
 *
 * @param value - Slate JSON value
 * @param onChange - Callback when content changes
 * @param placeholder - Placeholder text
 * @param disabled - Whether editor is disabled
 * @param readOnly - Whether editor is read-only
 * @param autoFocus - Whether to auto-focus on mount
 * @param minHeight - Minimum height CSS value
 * @param maxHeight - Maximum height CSS value
 * @param id - HTML id attribute
 * @param ariaLabel - Accessibility label
 * @param ariaDescribedBy - Accessibility description reference
 */
export function PlateEditor({
  value,
  onChange,
  placeholder,
  disabled = false,
  readOnly = false,
  autoFocus = false,
  minHeight = '200px',
  maxHeight,
  id,
  ariaLabel,
  ariaDescribedBy,
}: PlateEditorProps) {
  // Create plugins with markdown support
  const plugins = useMemo(() => createPlugins([
    // Block types
    createParagraphPlugin(),
    createHeadingPlugin(),
    createCodeBlockPlugin(),
    createBlockquotePlugin(),
    createListPlugin(),
    createHorizontalRulePlugin(),

    // Inline marks
    createBasicMarksPlugin(),
    createLinkPlugin(),

    // Autoformat (markdown shortcuts)
    createAutoformatPlugin({
      options: {
        rules: [
          // Headings
          { mode: 'block', type: 'h1', match: '# ' },
          { mode: 'block', type: 'h2', match: '## ' },
          { mode: 'block', type: 'h3', match: '### ' },

          // Lists
          { mode: 'block', type: 'ul', match: ['- ', '* '] },
          { mode: 'block', type: 'ol', match: '1. ' },

          // Blockquote
          { mode: 'block', type: 'blockquote', match: '> ' },

          // Code block
          { mode: 'block', type: 'code_block', match: '```' },

          // Marks
          { mode: 'mark', type: 'bold', match: '**' },
          { mode: 'mark', type: 'italic', match: '*' },
          { mode: 'mark', type: 'code', match: '`' },
        ]
      }
    })
  ]), []);

  // Handle value changes
  const handleChange = useCallback((newValue: SlateValue) => {
    onChange(newValue);
  }, [onChange]);

  return (
    <Plate
      plugins={plugins}
      value={value}
      onChange={handleChange}
    >
      <PlateContent
        id={id}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        autoFocus={autoFocus}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm overflow-y-auto"
        style={{
          minHeight,
          maxHeight: maxHeight || 'none',
        }}
      />
    </Plate>
  );
}

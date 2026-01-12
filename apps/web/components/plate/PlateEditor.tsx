/**
 * PlateEditor Component
 *
 * Wrapper component integrating installed @plate registry components.
 * Uses Editor from @/components/ui/editor and BaseEditorKit for plugins.
 */

'use client';

import * as React from 'react';
import { Plate, usePlateEditor } from 'platejs/react';
import { Editor, EditorContainer } from '@/components/ui/editor';
import { BaseEditorKit } from '@/components/editor/editor-base-kit';
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
 * PlateEditor - Thin wrapper around @plate components
 *
 * Provides a simplified API for markdown editing using the installed
 * @plate component system. Integrates Editor UI component with BaseEditorKit
 * plugin system.
 *
 * @param props - PlateEditorProps
 * @returns React component
 */
export function PlateEditor({
  value,
  onChange,
  placeholder,
  disabled = false,
  readOnly = false,
  autoFocus = false,
  minHeight,
  maxHeight,
  id,
  ariaLabel,
  ariaDescribedBy,
}: PlateEditorProps) {
  // Create editor instance with BaseEditorKit plugins
  const editor = usePlateEditor(
    {
      id: id || 'plate-editor',
      plugins: BaseEditorKit,
      value,
    },
    [value]
  );

  // Handle onChange from Plate
  const handleChange = React.useCallback(
    ({ value: newValue }: { value: SlateValue }) => {
      onChange(newValue);
    },
    [onChange]
  );

  // Build container styles
  const containerStyle = React.useMemo(() => {
    const style: React.CSSProperties = {};
    if (minHeight) style.minHeight = minHeight;
    if (maxHeight) style.maxHeight = maxHeight;
    return style;
  }, [minHeight, maxHeight]);

  return (
    <Plate editor={editor} onChange={handleChange} readOnly={readOnly}>
      <EditorContainer style={containerStyle}>
        <Editor
          id={id}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={readOnly}
          autoFocus={autoFocus}
          aria-label={ariaLabel}
          aria-describedby={ariaDescribedBy}
        />
      </EditorContainer>
    </Plate>
  );
}

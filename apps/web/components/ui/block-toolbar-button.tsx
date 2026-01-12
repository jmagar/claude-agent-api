'use client';

import * as React from 'react';

import type { TElement } from 'platejs';

import { useEditorRef, useSelectionFragmentProp } from 'platejs/react';

import { getBlockType, setBlockType } from '@/components/editor/transforms';

import { ToolbarButton } from './toolbar';

export interface BlockToolbarButtonProps
  extends Omit<React.ComponentProps<typeof ToolbarButton>, 'pressed'> {
  nodeType: string;
}

/**
 * Toolbar button for toggling block-level elements (headings, blockquotes, code blocks).
 *
 * Unlike MarkToolbarButton (for inline marks), this button:
 * - Uses setBlockType/getBlockType transforms
 * - Toggles between the specified block type and paragraph
 * - Shows pressed state when selection is in the target block type
 */
export function BlockToolbarButton({
  children,
  nodeType,
  ...props
}: BlockToolbarButtonProps) {
  const editor = useEditorRef();

  const currentBlockType = useSelectionFragmentProp({
    defaultValue: 'p',
    getProp: (node) => getBlockType(node as TElement),
  });

  const pressed = currentBlockType === nodeType;

  const handleClick = React.useCallback(() => {
    // Toggle: if already this type, convert to paragraph; otherwise convert to this type
    const targetType = pressed ? 'p' : nodeType;
    setBlockType(editor, targetType);
  }, [editor, nodeType, pressed]);

  return (
    <ToolbarButton pressed={pressed} onClick={handleClick} {...props}>
      {children}
    </ToolbarButton>
  );
}

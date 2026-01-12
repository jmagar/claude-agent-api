'use client';

import {
  BoldIcon,
  Code2Icon,
  FileCodeIcon,
  Heading1Icon,
  Heading2Icon,
  Heading3Icon,
  ItalicIcon,
  QuoteIcon,
  StrikethroughIcon,
} from 'lucide-react';
import { KEYS } from 'platejs';

import { BlockToolbarButton } from '@/components/ui/block-toolbar-button';
import { RedoToolbarButton, UndoToolbarButton } from '@/components/ui/history-toolbar-button';
import { LinkToolbarButton } from '@/components/ui/link-toolbar-button';
import {
  BulletedListToolbarButton,
  NumberedListToolbarButton,
} from '@/components/ui/list-toolbar-button';
import { MarkToolbarButton } from '@/components/ui/mark-toolbar-button';
import { Toolbar, ToolbarGroup } from '@/components/ui/toolbar';
import { cn } from '@/lib/utils';

export interface PlateMarkdownToolbarProps {
  className?: string;
}

export function PlateMarkdownToolbar({ className }: PlateMarkdownToolbarProps) {
  return (
    <Toolbar className={cn('flex w-full items-center', className)}>
      {/* History buttons */}
      <ToolbarGroup>
        <UndoToolbarButton />
        <RedoToolbarButton />
      </ToolbarGroup>

      {/* Mark buttons (inline formatting) */}
      <ToolbarGroup>
        <MarkToolbarButton nodeType={KEYS.bold} tooltip="Bold (⌘+B)">
          <BoldIcon />
        </MarkToolbarButton>

        <MarkToolbarButton nodeType={KEYS.italic} tooltip="Italic (⌘+I)">
          <ItalicIcon />
        </MarkToolbarButton>

        <MarkToolbarButton nodeType={KEYS.code} tooltip="Code (⌘+E)">
          <Code2Icon />
        </MarkToolbarButton>

        <MarkToolbarButton
          nodeType={KEYS.strikethrough}
          tooltip="Strikethrough (⌘+⇧+M)"
        >
          <StrikethroughIcon />
        </MarkToolbarButton>
      </ToolbarGroup>

      {/* Heading buttons (block elements) */}
      <ToolbarGroup>
        <BlockToolbarButton nodeType="h1" tooltip="Heading 1">
          <Heading1Icon />
        </BlockToolbarButton>

        <BlockToolbarButton nodeType="h2" tooltip="Heading 2">
          <Heading2Icon />
        </BlockToolbarButton>

        <BlockToolbarButton nodeType="h3" tooltip="Heading 3">
          <Heading3Icon />
        </BlockToolbarButton>
      </ToolbarGroup>

      {/* List buttons */}
      <ToolbarGroup>
        <BulletedListToolbarButton />
        <NumberedListToolbarButton />
      </ToolbarGroup>

      {/* Block buttons */}
      <ToolbarGroup>
        <BlockToolbarButton nodeType={KEYS.codeBlock} tooltip="Code Block">
          <FileCodeIcon />
        </BlockToolbarButton>

        <BlockToolbarButton nodeType={KEYS.blockquote} tooltip="Blockquote">
          <QuoteIcon />
        </BlockToolbarButton>

        <LinkToolbarButton />
      </ToolbarGroup>
    </Toolbar>
  );
}

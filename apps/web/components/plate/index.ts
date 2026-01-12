/**
 * Plate Components Barrel Export
 *
 * Re-exports all Plate-related components and hooks for easier imports.
 */

export { PlateEditor } from './PlateEditor';
export type { PlateEditorProps } from './PlateEditor';

export { PlateMarkdownToolbar } from './PlateMarkdownToolbar';
export type { PlateMarkdownToolbarProps } from './PlateMarkdownToolbar';

export { PlateMarkdownEditor } from './PlateMarkdownEditor';
export type { PlateMarkdownEditorProps } from './PlateMarkdownEditor';

export { PlateYamlEditor } from './PlateYamlEditor';
export type { PlateYamlEditorProps } from './PlateYamlEditor';

export { PlateJsonEditor } from './PlateJsonEditor';
export type { PlateJsonEditorProps } from './PlateJsonEditor';

export { useMarkdownSync } from './hooks/useMarkdownSync';
export type { UseMarkdownSyncReturn } from './hooks/useMarkdownSync';

export { useYamlFrontmatter } from './hooks/useYamlFrontmatter';
export type { UseYamlFrontmatterReturn } from './hooks/useYamlFrontmatter';

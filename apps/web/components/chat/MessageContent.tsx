/**
 * MessageContent component
 *
 * Renders text content with markdown support (bold, italic, code, links, lists).
 * Used by MessageItem to display text blocks.
 *
 * @see tests/unit/components/MessageItem.test.tsx for test specifications
 */

"use client";

export interface MessageContentProps {
  /** Markdown text to render */
  text: string;
}

export function MessageContent({ text }: MessageContentProps) {
  // Simple markdown parser for basic formatting
  // Full markdown library can be added later if needed

  // Parse bold: **text** -> <strong>text</strong>
  let html = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Parse italic: *text* -> <em>text</em>
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Parse inline code: `text` -> <code>text</code>
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  // Parse links: [text](url) -> <a href="url">text</a>
  html = html.replace(
    /\[(.+?)\]\((.+?)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );

  return (
    <div
      className="text-14 leading-relaxed text-gray-700 prose prose-sm max-w-none"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

/**
 * MessageContent component
 *
 * Renders text content with markdown support (bold, italic, code, links, lists).
 * Used by MessageItem to display text blocks.
 *
 * Security: Uses react-markdown with rehype-sanitize to prevent XSS attacks.
 * Links are restricted to http/https protocols only.
 *
 * @see tests/unit/components/MessageItem.test.tsx for test specifications
 */

"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import type { Components } from "react-markdown";

export interface MessageContentProps {
  /** Markdown text to render */
  text: string;
}

export function MessageContent({ text }: MessageContentProps) {
  // Custom components for secure link rendering
  const components: Components = {
    a: ({ node, href, children, ...props }) => {
      // Only allow http and https protocols
      const isValidProtocol =
        href && (href.startsWith("http://") || href.startsWith("https://"));

      if (!isValidProtocol) {
        // Render as plain text if protocol is invalid
        return <span>{children}</span>;
      }

      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          {...props}
        >
          {children}
        </a>
      );
    },
  };

  return (
    <div className="text-14 leading-relaxed text-gray-700 prose prose-sm max-w-none">
      <ReactMarkdown
        rehypePlugins={[rehypeSanitize]}
        components={components}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

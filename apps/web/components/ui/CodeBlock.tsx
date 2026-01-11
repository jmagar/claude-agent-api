/**
 * CodeBlock component
 *
 * Reusable syntax-highlighted code block using react-syntax-highlighter.
 * Supports JSON, TypeScript, JavaScript, and other languages.
 */

"use client";

import { memo, lazy, Suspense } from "react";

export type CodeLanguage = "json" | "typescript" | "javascript" | "bash" | "text";

export interface CodeBlockProps {
  code: string;
  language?: CodeLanguage;
  className?: string;
  showLineNumbers?: boolean;
}

/**
 * Format a value for display in code block
 */
export function formatCodeValue(value: unknown): string {
  if (typeof value === "string") {
    // Try to parse as JSON for pretty printing
    try {
      const parsed = JSON.parse(value);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value, null, 2);
}

// Lazy load the syntax highlighter component to avoid SSR and test issues
const SyntaxHighlighterWrapper = lazy(() =>
  import("./SyntaxHighlighterWrapper").then((mod) => ({
    default: mod.SyntaxHighlighterWrapper,
  }))
);

// Simple pre fallback component
const SimplePre = memo(function SimplePre({
  code,
  className = "",
}: {
  code: string;
  className?: string;
}) {
  return (
    <pre
      className={`bg-gray-50 p-8 rounded text-12 overflow-x-auto font-mono ${className}`}
      data-testid="code-block"
    >
      <code>{code}</code>
    </pre>
  );
});

export const CodeBlock = memo(function CodeBlock({
  code,
  language = "json",
  className = "",
  showLineNumbers = false,
}: CodeBlockProps) {
  // Use plain pre for very short code or plain text
  if (language === "text" || code.length < 10) {
    return <SimplePre code={code} className={className} />;
  }

  // Check if we're in a test environment
  if (typeof window === "undefined" || process.env.NODE_ENV === "test") {
    return <SimplePre code={code} className={className} />;
  }

  return (
    <Suspense fallback={<SimplePre code={code} className={className} />}>
      <div data-testid="code-block" className={className}>
        <SyntaxHighlighterWrapper
          code={code}
          language={language}
          showLineNumbers={showLineNumbers}
        />
      </div>
    </Suspense>
  );
});

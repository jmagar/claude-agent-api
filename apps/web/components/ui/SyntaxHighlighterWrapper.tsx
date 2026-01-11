/**
 * SyntaxHighlighterWrapper component
 *
 * Isolated wrapper for react-syntax-highlighter to enable lazy loading
 * and avoid SSR/test environment issues.
 */

"use client";

import { memo } from "react";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import json from "react-syntax-highlighter/dist/esm/languages/hljs/json";
import typescript from "react-syntax-highlighter/dist/esm/languages/hljs/typescript";
import javascript from "react-syntax-highlighter/dist/esm/languages/hljs/javascript";
import bash from "react-syntax-highlighter/dist/esm/languages/hljs/bash";
import { atomOneLight } from "react-syntax-highlighter/dist/esm/styles/hljs";
import type { CodeLanguage } from "./CodeBlock";

// Register languages for tree-shaking
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("typescript", typescript);
SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("bash", bash);

export interface SyntaxHighlighterWrapperProps {
  code: string;
  language: CodeLanguage;
  showLineNumbers?: boolean;
}

export const SyntaxHighlighterWrapper = memo(function SyntaxHighlighterWrapper({
  code,
  language,
  showLineNumbers = false,
}: SyntaxHighlighterWrapperProps) {
  return (
    <SyntaxHighlighter
      language={language}
      style={atomOneLight}
      showLineNumbers={showLineNumbers}
      customStyle={{
        margin: 0,
        padding: "8px",
        borderRadius: "4px",
        fontSize: "12px",
        backgroundColor: "rgb(249 250 251)", // gray-50
      }}
      codeTagProps={{
        style: {
          fontFamily: "ui-monospace, monospace",
        },
      }}
    >
      {code}
    </SyntaxHighlighter>
  );
});

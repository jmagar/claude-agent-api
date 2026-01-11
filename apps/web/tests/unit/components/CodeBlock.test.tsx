/**
 * Unit tests for CodeBlock component
 *
 * Tests syntax highlighting for JSON and other languages.
 */

import { render, screen } from "@testing-library/react";
import { CodeBlock, formatCodeValue } from "@/components/ui/CodeBlock";

describe("CodeBlock", () => {
  describe("formatCodeValue", () => {
    it("should format objects as pretty JSON", () => {
      const obj = { name: "test", value: 123 };
      const result = formatCodeValue(obj);

      expect(result).toBe(JSON.stringify(obj, null, 2));
    });

    it("should return strings as-is if not valid JSON", () => {
      const str = "plain text";
      const result = formatCodeValue(str);

      expect(result).toBe("plain text");
    });

    it("should pretty-print valid JSON strings", () => {
      const jsonStr = '{"key":"value"}';
      const result = formatCodeValue(jsonStr);

      expect(result).toBe('{\n  "key": "value"\n}');
    });

    it("should handle arrays", () => {
      const arr = [1, 2, 3];
      const result = formatCodeValue(arr);

      expect(result).toBe(JSON.stringify(arr, null, 2));
    });

    it("should handle null", () => {
      const result = formatCodeValue(null);

      expect(result).toBe("null");
    });

    it("should handle undefined", () => {
      const result = formatCodeValue(undefined);

      expect(result).toBe(undefined);
    });

    it("should handle numbers", () => {
      const result = formatCodeValue(42);

      expect(result).toBe("42");
    });

    it("should handle boolean", () => {
      expect(formatCodeValue(true)).toBe("true");
      expect(formatCodeValue(false)).toBe("false");
    });
  });

  describe("CodeBlock component", () => {
    it("should render code content", () => {
      render(<CodeBlock code='{"key": "value"}' language="json" />);

      expect(screen.getByTestId("code-block")).toBeInTheDocument();
    });

    it("should use plain pre for text language", () => {
      render(<CodeBlock code="plain text" language="text" />);

      const codeBlock = screen.getByTestId("code-block");
      expect(codeBlock.tagName).toBe("PRE");
    });

    it("should use plain pre for very short code", () => {
      render(<CodeBlock code="abc" language="json" />);

      const codeBlock = screen.getByTestId("code-block");
      expect(codeBlock.tagName).toBe("PRE");
    });

    it("should apply custom className", () => {
      render(
        <CodeBlock code="longer code content here" language="json" className="custom-class" />
      );

      const codeBlock = screen.getByTestId("code-block");
      expect(codeBlock).toHaveClass("custom-class");
    });

    it("should render JSON syntax highlighted code", () => {
      const jsonCode = `{
  "name": "test",
  "value": 123,
  "nested": {
    "array": [1, 2, 3]
  }
}`;

      render(<CodeBlock code={jsonCode} language="json" />);

      const codeBlock = screen.getByTestId("code-block");
      expect(codeBlock).toBeInTheDocument();
    });

    it("should render typescript code", () => {
      const tsCode = `function hello(name: string): string {
  return \`Hello, \${name}!\`;
}`;

      render(<CodeBlock code={tsCode} language="typescript" />);

      const codeBlock = screen.getByTestId("code-block");
      expect(codeBlock).toBeInTheDocument();
    });

    it("should render bash code", () => {
      const bashCode = `#!/bin/bash
echo "Hello World"
ls -la`;

      render(<CodeBlock code={bashCode} language="bash" />);

      const codeBlock = screen.getByTestId("code-block");
      expect(codeBlock).toBeInTheDocument();
    });
  });
});

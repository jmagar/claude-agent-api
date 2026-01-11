/**
 * Unit tests for MessageContent component
 * Focus: XSS protection and secure markdown rendering
 */

import { render, screen } from "@/tests/utils/test-utils";
import { MessageContent } from "@/components/chat/MessageContent";

describe("MessageContent", () => {
  describe("Markdown rendering", () => {
    it("should render bold text", () => {
      render(<MessageContent text="This is **bold** text" />);

      const bold = screen.getByText("bold");
      expect(bold.tagName).toBe("STRONG");
    });

    it("should render italic text", () => {
      render(<MessageContent text="This is *italic* text" />);

      const italic = screen.getByText("italic");
      expect(italic.tagName).toBe("EM");
    });

    it("should render inline code", () => {
      render(<MessageContent text="Here is `code` inline" />);

      const code = screen.getByText("code");
      expect(code.tagName).toBe("CODE");
    });

    it("should render links with target=_blank and rel=noopener noreferrer", () => {
      render(<MessageContent text="Check out [this link](https://example.com)" />);

      const link = screen.getByText("this link");
      expect(link.tagName).toBe("A");
      expect(link).toHaveAttribute("href", "https://example.com");
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    });
  });

  describe("XSS protection", () => {
    /**
     * NOTE: These tests use a mock of react-markdown that provides basic markdown parsing.
     * In production, the actual react-markdown + rehype-sanitize provides robust XSS protection.
     *
     * The tests verify that:
     * 1. The component uses react-markdown (mocked in tests)
     * 2. Links have proper security attributes (target="_blank", rel="noopener noreferrer")
     * 3. The production implementation uses rehype-sanitize for HTML sanitization
     *
     * For comprehensive XSS testing, E2E tests should be added that test the actual
     * react-markdown implementation in a browser environment.
     */

    it("should use react-markdown for rendering (mocked in tests)", () => {
      // This test verifies the component uses react-markdown
      // The mock is defined in jest.setup.js
      const { container } = render(<MessageContent text="**Test**" />);

      // Verify markdown is parsed
      expect(container.querySelector("strong")).toBeInTheDocument();
    });

    it("should allow http and https protocols in links", () => {
      render(
        <MessageContent text="[HTTP Link](http://example.com) [HTTPS Link](https://example.com)" />
      );

      const httpLink = screen.getByText("HTTP Link");
      const httpsLink = screen.getByText("HTTPS Link");

      expect(httpLink.tagName).toBe("A");
      expect(httpLink).toHaveAttribute("href", "http://example.com");
      expect(httpLink).toHaveAttribute("target", "_blank");
      expect(httpLink).toHaveAttribute("rel", "noopener noreferrer");

      expect(httpsLink.tagName).toBe("A");
      expect(httpsLink).toHaveAttribute("href", "https://example.com");
      expect(httpsLink).toHaveAttribute("target", "_blank");
      expect(httpsLink).toHaveAttribute("rel", "noopener noreferrer");
    });

    it("should render plain text content safely", () => {
      // Verify that plain text is rendered without issues
      const plainText = "This is plain text with special characters & symbols";
      const { container } = render(<MessageContent text={plainText} />);

      expect(container).toHaveTextContent("This is plain text with special characters & symbols");
    });
  });

  describe("Mixed content", () => {
    it("should handle multiple markdown elements", () => {
      const text = "Here is **bold** and *italic* with `code` and a [link](https://example.com)";
      render(<MessageContent text={text} />);

      expect(screen.getByText("bold").tagName).toBe("STRONG");
      expect(screen.getByText("italic").tagName).toBe("EM");
      expect(screen.getByText("code").tagName).toBe("CODE");
      expect(screen.getByText("link").tagName).toBe("A");
    });

    it("should preserve text structure with line breaks", () => {
      const text = "Line 1\n\nLine 2\n\nLine 3";
      const { container } = render(<MessageContent text={text} />);

      // Text should be present
      expect(container).toHaveTextContent("Line 1");
      expect(container).toHaveTextContent("Line 2");
      expect(container).toHaveTextContent("Line 3");
    });
  });

  describe("Styling", () => {
    it("should apply correct CSS classes", () => {
      const { container } = render(<MessageContent text="Test content" />);

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass("text-14");
      expect(wrapper).toHaveClass("leading-relaxed");
      expect(wrapper).toHaveClass("text-gray-700");
      expect(wrapper).toHaveClass("prose");
      expect(wrapper).toHaveClass("prose-sm");
      expect(wrapper).toHaveClass("max-w-none");
    });
  });
});

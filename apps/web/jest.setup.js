/**
 * Jest setup file
 * Mocks browser APIs and polyfills for Node environment
 */

import "@testing-library/jest-dom";
import "whatwg-fetch";
import { TransformStream, ReadableStream, WritableStream } from "stream/web";
import { TextEncoder, TextDecoder } from "util";

// Polyfill TextEncoder/TextDecoder for msw
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Polyfill Response.json for NextResponse.json usage in tests
if (typeof Response.json !== "function") {
  Response.json = (data, init = {}) => {
    const headers = new Headers(init.headers);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    return new Response(JSON.stringify(data), {
      ...init,
      headers,
    });
  };
}

// Mock window.matchMedia for SettingsContext
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

global.localStorage = localStorageMock;

// Mock scrollIntoView for MessageList
Element.prototype.scrollIntoView = jest.fn();

// Mock ResizeObserver for virtualization components
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = ResizeObserverMock;

// Mock requestAnimationFrame for virtualization
global.requestAnimationFrame = (callback) => setTimeout(callback, 0);
global.cancelAnimationFrame = (id) => clearTimeout(id);

// Polyfill Web Streams for MSW in jsdom
global.TransformStream = TransformStream;
global.ReadableStream = ReadableStream;
global.WritableStream = WritableStream;

// Mock BroadcastChannel for MSW
class BroadcastChannelMock {
  constructor() {}
  postMessage() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
}

global.BroadcastChannel = BroadcastChannelMock;

// Mock rehype-sanitize (not needed in tests since we're mocking react-markdown)
jest.mock("rehype-sanitize", () => ({
  __esModule: true,
  default: () => {},
}));

// Mock react-virtuoso for deterministic rendering in tests
jest.mock("react-virtuoso", () => ({
  Virtuoso: ({ data = [], itemContent, components = {} }) => {
    const Scroller = components.Scroller || (({ children, ...props }) => <div {...props}>{children}</div>);
    const List = components.List || (({ children, ...props }) => <div {...props}>{children}</div>);
    const Footer = components.Footer || (() => null);

    return (
      <Scroller data-virtuoso-scroller="true">
        <List data-testid="virtuoso-item-list">
          {data.map((item, index) => (
            <div key={item?.id ?? index}>{itemContent(index, item)}</div>
          ))}
          <Footer />
        </List>
      </Scroller>
    );
  },
}));

// Mock react-markdown for preview rendering in tests
jest.mock("react-markdown", () => {
  return function ReactMarkdown({ children, className }) {
    // Simple markdown-to-text conversion for testing
    // Preserve text content but strip markdown formatting
    if (typeof children !== 'string') {
      return <div className={className}>{children}</div>;
    }

    const text = children
      .replace(/^#{1,6}\s+(.+)$/gm, '$1')  // Headings: # Text → Text
      .replace(/\*\*(.+?)\*\*/g, '$1')      // Bold: **text** → text
      .replace(/\*(.+?)\*/g, '$1')          // Italic: *text* → text
      .replace(/`(.+?)`/g, '$1')            // Code: `text` → text
      .replace(/^\s*[-*]\s+/gm, '')         // List markers
      .trim();

    return <div className={className}>{text}</div>;
  };
});

// Reset mocks before each test
beforeEach(() => {
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
});

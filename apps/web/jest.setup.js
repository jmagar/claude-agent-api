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

// Mock react-markdown to avoid ESM transformation issues
jest.mock("react-markdown", () => {
  return {
    __esModule: true,
    default: ({ children }) => {
      // Simple markdown parser for tests
      let html = children;

      // Parse bold: **text** -> <strong>text</strong>
      html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

      // Parse italic: *text* -> <em>text</em>
      html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

      // Parse inline code: `text` -> <code>text</code>
      html = html.replace(/`(.+?)`/g, "<code>$1</code>");

      // Parse links: [text](url) -> <a href="url">text</a>
      html = html.replace(
        /\[(.+?)\]\((.+?)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
      );

      return <div dangerouslySetInnerHTML={{ __html: html }} />;
    },
  };
});

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

// Reset mocks before each test
beforeEach(() => {
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
});

/**
 * Jest setup file
 * Mocks browser APIs and polyfills for Node environment
 */

import "@testing-library/jest-dom";
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

// Reset mocks before each test
beforeEach(() => {
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
});

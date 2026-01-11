import js from "@eslint/js";
import typescript from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";
import next from "@next/eslint-plugin-next";

export default [
  js.configs.recommended,
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
    plugins: {
      "@typescript-eslint": typescript,
      react,
      "react-hooks": reactHooks,
      "jsx-a11y": jsxA11y,
      "@next/next": next,
    },
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        React: "writable",
        JSX: "writable",
        // Browser globals
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        console: "readonly",
        fetch: "readonly",
        URLSearchParams: "readonly",
        Element: "readonly",
        HTMLElement: "readonly",
        HTMLInputElement: "readonly",
        HTMLButtonElement: "readonly",
        HTMLTextAreaElement: "readonly",
        HTMLDivElement: "readonly",
        HTMLSpanElement: "readonly",
        localStorage: "readonly",
        sessionStorage: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        AbortController: "readonly",
        Headers: "readonly",
        RequestInit: "readonly",
        KeyboardEvent: "readonly",
        // Node.js globals
        process: "readonly",
        Buffer: "readonly",
        __dirname: "readonly",
        __filename: "readonly",
        module: "readonly",
        require: "readonly",
        global: "readonly",
        // Jest/Testing globals
        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        jest: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
      },
    },
    settings: {
      react: {
        version: "detect",
      },
      next: {
        rootDir: "apps/web/",
      },
    },
    rules: {
      // Core JavaScript/TypeScript rules from original config
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "prefer-const": "error",
      "no-var": "error",

      // Next.js Core Web Vitals rules
      ...next.configs.recommended.rules,
      ...next.configs["core-web-vitals"].rules,

      // React recommended rules
      ...react.configs.recommended.rules,
      ...react.configs["jsx-runtime"].rules,

      // React Hooks rules
      ...reactHooks.configs.recommended.rules,

      // JSX Accessibility rules
      ...jsxA11y.configs.recommended.rules,

      // TypeScript recommended rules
      ...typescript.configs.recommended.rules,
    },
  },
  {
    files: ["**/*.js", "**/*.mjs"],
    rules: {
      "@typescript-eslint/no-var-requires": "off",
    },
  },
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "out/**",
      "build/**",
      "dist/**",
      ".turbo/**",
      "coverage/**",
    ],
  },
];

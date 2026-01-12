const nextJest = require("next/jest");

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: "./",
});

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  testEnvironmentOptions: {
    customExportConditions: ["node", "node-addons"],
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    "^@udecode/plate-core/react$": "<rootDir>/tests/__mocks__/@udecode/plate-core.tsx",
    "^@udecode/plate-core$": "<rootDir>/tests/__mocks__/@udecode/plate-core.tsx",
    "^@udecode/plate-paragraph$": "<rootDir>/tests/__mocks__/@udecode/plate-paragraph.ts",
    "^@udecode/plate-heading$": "<rootDir>/tests/__mocks__/@udecode/plate-heading.ts",
    "^@udecode/plate-basic-marks$": "<rootDir>/tests/__mocks__/@udecode/plate-basic-marks.ts",
    "^@udecode/plate-list$": "<rootDir>/tests/__mocks__/@udecode/plate-list.ts",
    "^@udecode/plate-code-block$": "<rootDir>/tests/__mocks__/@udecode/plate-code-block.ts",
    "^@udecode/plate-block-quote$": "<rootDir>/tests/__mocks__/@udecode/plate-block-quote.ts",
    "^@udecode/plate-link$": "<rootDir>/tests/__mocks__/@udecode/plate-link.ts",
    "^@udecode/plate-horizontal-rule$": "<rootDir>/tests/__mocks__/@udecode/plate-horizontal-rule.ts",
    "^@udecode/plate-autoformat$": "<rootDir>/tests/__mocks__/@udecode/plate-autoformat.ts",
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(.pnpm|msw|@mswjs|open-draft|until-async|headers-polyfill|react-syntax-highlighter|refractor|hast-util-to-html|property-information|space-separated-tokens|comma-separated-tokens|hast-util-whitespace|@udecode|nanoid|slate|slate-react|slate-history|slate-dom))",
  ],
  testMatch: [
    "<rootDir>/tests/unit/**/*.test.{ts,tsx}",
    "<rootDir>/tests/integration/**/*.test.{ts,tsx}",
  ],
  collectCoverageFrom: [
    "app/**/*.{ts,tsx}",
    "components/**/*.{ts,tsx}",
    "lib/**/*.{ts,tsx}",
    "hooks/**/*.{ts,tsx}",
    "contexts/**/*.{ts,tsx}",
    "!**/*.d.ts",
    "!**/node_modules/**",
    "!**/.next/**",
  ],
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 85,
      lines: 85,
      statements: 85,
    },
  },
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig);

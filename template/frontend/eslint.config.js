import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import jsxA11y from 'eslint-plugin-jsx-a11y'

// React rules apply to app code only: Playwright fixtures call `use()`, which
// react-hooks would report as a hook call.
const reactFiles = ['src/**/*.{ts,tsx}']

// This project is tested only end to end, against the real stack (e2e/).
// These rules make a mock, a fake backend or a unit-test runner a lint error.
const NO_MOCKS =
  'Tests here run end to end against the real backend and database (see e2e/fixtures.ts): no mocks, fakes or unit-test runners.'

const mockAndUnitTestLibraries = [
  'msw',
  'msw/*',
  '@mswjs/*',
  'playwright-msw',
  'nock',
  'sinon',
  'fetch-mock',
  '*-fetch-mock',
  'axios-mock-adapter',
  'miragejs',
  'pretender',
  'json-server',
  'vitest',
  'vitest/*',
  '@vitest/*',
  'jest',
  '@jest/*',
  '@testing-library/*',
  'jsdom',
  'happy-dom',
]

const noMockImports = { group: mockAndUnitTestLibraries, message: NO_MOCKS }

// Playwright APIs that fake or rewrite network traffic, or replace page code.
const networkFakes = ['route', 'routeFromHAR', 'unroute', 'unrouteAll', 'routeWebSocket']
// Browser network APIs a test could replace in the page.
const networkApis = '/^(fetch|XMLHttpRequest|WebSocket|EventSource)$/'
const networkNames = `/^(fetch|XMLHttpRequest|WebSocket|EventSource|${networkFakes.join('|')}|fulfill)$/`

// Files ESLint checks with the e2e rules: everything Playwright or Node could load.
const e2eFiles = 'e2e/**/*.{ts,tsx,mts,cts,js,jsx,mjs,cjs}'

const USE_FIXTURES =
  "Import from './fixtures' (types too): every spec runs on the shared real-stack fixtures."
// Every package that exposes Playwright's test runner or browser API.
const playwrightEntryPoints = [
  '@playwright/test',
  'playwright',
  'playwright/test',
  'playwright-core',
]
const playwrightSubpaths = ['@playwright/*', 'playwright/*', 'playwright-core/*']

export default [
  {
    ignores: [
      'node_modules/**',
      '.output/**',
      '.tanstack/**',
      'dist/**',
      'build/**',
      'playwright-report/**',
      'test-results/**',
      'blob-report/**',
      '*.config.ts',
      '*.config.js',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...[
    react.configs.flat.recommended,
    react.configs.flat['jsx-runtime'],
    reactHooks.configs.flat.recommended,
    jsxA11y.flatConfigs.recommended,
  ].map(config => ({ ...config, files: reactFiles })),
  {
    files: reactFiles,
    rules: {
      // TypeScript types the props, so runtime prop-types are redundant.
      'react/prop-types': 'off',
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  {
    files: ['**/*.{ts,tsx,js,jsx}'],
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
      'no-restricted-imports': ['error', { patterns: [noMockImports] }],
    },
  },
  {
    // Every file type Playwright or Node could load from e2e/, not only .ts.
    files: [e2eFiles],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: playwrightEntryPoints.map(name => ({ name, message: USE_FIXTURES })),
          patterns: [noMockImports, { group: playwrightSubpaths, message: USE_FIXTURES }],
        },
      ],
      'no-restricted-properties': [
        'error',
        ...[...networkFakes, 'fulfill'].map(property => ({
          property,
          message: `${NO_MOCKS} ${property}() fakes the backend; seed data through the real API instead.`,
        })),
        {
          property: 'addInitScript',
          message: `${NO_MOCKS} Init scripts can stub fetch in the page. To sign in, use the authedPage or loginAs fixture.`,
        },
        {
          property: 'addScriptTag',
          message: `${NO_MOCKS} Injected scripts can stub fetch in the page.`,
        },
        {
          property: 'waitForTimeout',
          message: 'Do not sleep. Wait for the visible result with expect(...), which retries.',
        },
      ],
      'no-restricted-syntax': [
        'error',
        // Replacing the browser's network APIs: window.fetch = …, window['fetch'] = …,
        // Object.assign(window, { fetch }), Reflect.set(window, 'fetch', …), defineProperty(…).
        {
          selector: `AssignmentExpression > MemberExpression.left[property.name=${networkApis}]`,
          message: `${NO_MOCKS} Do not replace the browser's network APIs.`,
        },
        {
          selector: `Property[key.name=${networkApis}]`,
          message: `${NO_MOCKS} Do not replace the browser's network APIs.`,
        },
        // Any string naming a network API or a Playwright interception method:
        // catches window['fetch'], Reflect.set(…, 'fetch'), and
        // `const r = 'route'; (page as any)[r](…)`.
        {
          selector: `Literal[value=${networkNames}]`,
          message: `${NO_MOCKS} Do not reach network APIs or route() by name.`,
        },
        {
          selector: `TemplateElement[value.cooked=${networkNames}]`,
          message: `${NO_MOCKS} Do not reach network APIs or route() by name.`,
        },
        // page.evaluate('window.fetch = …') hides code from these rules: pass a function.
        {
          selector:
            'CallExpression[callee.property.name=/^(evaluate|evaluateHandle|evaluateAll|\\$eval|\\$\\$eval)$/] > :matches(Literal, TemplateLiteral).arguments:first-child',
          message: 'Pass a function to evaluate(), not a string of code, so lint can check it.',
        },
        {
          selector: 'ImportExpression',
          message: `${USE_FIXTURES} Use static imports.`,
        },
        {
          selector: "CallExpression[callee.name='require']",
          message: `${USE_FIXTURES} Use static imports.`,
        },
        // Every test runs, every time. A test that cannot pass is a bug to fix or delete.
        {
          selector: 'MemberExpression[property.name=/^(skip|fixme|only|fail)$/]',
          message:
            'Do not skip, fixme, fail or focus tests. If you truly must, add an eslint-disable-next-line comment that says why.',
        },
      ],
    },
  },
  {
    // fixtures.ts is the one file that wraps @playwright/test for the specs.
    files: ['e2e/fixtures.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: playwrightEntryPoints
            .filter(name => name !== '@playwright/test')
            .map(name => ({ name, message: USE_FIXTURES })),
          patterns: [
            noMockImports,
            { group: [...playwrightSubpaths, '!@playwright/test'], message: USE_FIXTURES },
          ],
        },
      ],
    },
  },
  {
    // Generic <label> wrapper: callers associate it with a control via htmlFor.
    files: ['src/components/ui/label.tsx'],
    rules: {
      'jsx-a11y/label-has-associated-control': 'off',
    },
  },
]

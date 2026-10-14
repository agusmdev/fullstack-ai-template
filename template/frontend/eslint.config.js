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
// Browser network APIs a test could replace or patch in the page.
const networkApiNames = 'fetch|XMLHttpRequest|WebSocket|EventSource|Response|Request|Headers'
const networkApis = `/^(${networkApiNames})$/`
// Chrome DevTools Protocol sessions: Fetch.fulfillRequest fakes any response.
const cdpSessions = ['newCDPSession', 'newBrowserCDPSession']
const networkNames = `/^(${networkApiNames}|${[...networkFakes, ...cdpSessions].join('|')}|fulfill)$/`
// Network classes whose prototype a test could patch: Response.prototype.json = …
const networkClasses = '/^(XMLHttpRequest|WebSocket|EventSource|Response|Request|Headers)$/'

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
const PLAYWRIGHT_IN_E2E_ONLY =
  'Playwright belongs in e2e/ only, where lint checks it for network fakes. Do not put test helpers in app code.'
const noPlaywrightImports = {
  patterns: [
    noMockImports,
    { group: [...playwrightEntryPoints, ...playwrightSubpaths], message: PLAYWRIGHT_IN_E2E_ONLY },
  ],
}

// App code that specs may import. Anything else under src/ could hide a
// network fake from the e2e rules, so specs cannot import it.
const SRC_IMPORTS =
  'Specs may import only API endpoints, auth constants and types from src/. Put test helpers in e2e/.'
const restrictedSrcImports = {
  regex: '^(@/|(\\.\\./)+src/)(?!(lib/api-endpoints|lib/auth|types/[\\w-]+)$)',
  message: SRC_IMPORTS,
}

// Playwright methods that fake the backend, inject page code or render fake HTML.
const fakingProperties = [
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
  ...cdpSessions.map(property => ({
    property,
    message: `${NO_MOCKS} A CDP session can intercept and fake network traffic (Fetch.fulfillRequest).`,
  })),
  {
    property: 'setContent',
    message: `${NO_MOCKS} setContent() renders fake HTML in place of the app; open a real page with goto().`,
  },
]

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
      'no-restricted-imports': ['error', noPlaywrightImports],
      'no-restricted-properties': ['error', ...fakingProperties],
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
          patterns: [
            noMockImports,
            restrictedSrcImports,
            { group: playwrightSubpaths, message: USE_FIXTURES },
          ],
        },
      ],
      'no-restricted-properties': [
        'error',
        ...fakingProperties,
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
        // Patching a network class: Response.prototype.json = …, XMLHttpRequest.prototype.open = …,
        // window.Response.prototype, Object.defineProperty(Response.prototype, …).
        {
          selector: `MemberExpression[property.name='prototype']:matches([object.name=${networkClasses}], [object.property.name=${networkClasses}])`,
          message: `${NO_MOCKS} Do not patch the browser's network classes.`,
        },
        // A string naming a network API or a Playwright interception method, used
        // to reach it: window['fetch'], Reflect.set(…, 'fetch'),
        // `const r = 'route'; (page as any)[r](…)`. Plain strings such as
        // resourceType() === 'fetch' or { name: 'Request' } are fine.
        ...[
          `MemberExpression[computed=true] > Literal.property[value=${networkNames}]`,
          `MemberExpression[computed=true] > TemplateLiteral.property > TemplateElement[value.cooked=${networkNames}]`,
          `CallExpression[callee.object.name=/^(Reflect|Object)$/] > Literal[value=${networkNames}]`,
          `VariableDeclarator > Literal.init[value=${networkNames}]`,
          `VariableDeclarator > TemplateLiteral.init > TemplateElement[value.cooked=${networkNames}]`,
        ].map(selector => ({
          selector,
          message: `${NO_MOCKS} Do not reach network APIs or route() by name.`,
        })),
        // CDP network commands ('Fetch.enable', 'Fetch.fulfillRequest', 'Network.…'),
        // in case a CDP session is reached another way.
        {
          selector: String.raw`:matches(Literal[value=/^(Fetch|Network)\./], TemplateElement[value.cooked=/^(Fetch|Network)\./])`,
          message: `${NO_MOCKS} Do not send CDP network commands.`,
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
        // retries: 0 in playwright.config.ts. A flaky test is a bug to fix, not to
        // retry: test.describe.configure({ retries }) would hide it.
        {
          selector: "Property:matches([key.name='retries'], [key.value='retries'])",
          message: 'Do not set retries. A flaky test is a bug to fix, not to retry.',
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
            restrictedSrcImports,
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

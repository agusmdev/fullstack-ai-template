/**
 * Guards for the test suite itself. They read files, not the app.
 * They also check that every page route and every backend endpoint in
 * src/lib/api-endpoints.ts is used by a spec.
 * ESLint (eslint.config.js) adds the code-level guards: no page.route() & co.,
 * no mock libraries, and specs import from './fixtures' only.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'
import { API } from '../src/lib/api-endpoints'
import { test, expect } from './fixtures'

const fromFrontend = (path: string) => fileURLToPath(new URL(`../${path}`, import.meta.url))

/** The code of a file without its comments: a path in a comment is not a test. */
function codeOf(file: string): string {
  const source = readFileSync(fromFrontend(file), 'utf8')
  return ts.transpileModule(source, {
    compilerOptions: { removeComments: true, target: ts.ScriptTarget.ESNext },
  }).outputText
}

// Recursive: Playwright's testMatch ('**/*.spec.ts') also runs specs in subfolders.
const specs = readdirSync(fromFrontend('e2e'), { recursive: true, encoding: 'utf8' })
  .map(file => file.split('\\').join('/'))
  .filter(file => file.endsWith('.spec.ts') && file !== 'guards.spec.ts')
  .map(file => ({ file, source: codeOf(`e2e/${file}`) }))

/** Page paths from the generated TanStack Router tree, e.g. '/', '/items', '/items/$itemId'. */
function appRoutes(): string[] {
  const routeTree = readFileSync(fromFrontend('src/routeTree.gen.ts'), 'utf8')
  const block = /export interface FileRoutesByFullPath \{([^}]*)\}/.exec(routeTree)?.[1]
  if (!block) throw new Error('FileRoutesByFullPath not found in src/routeTree.gen.ts')
  return [...block.matchAll(/'([^']+)':/g)].map(match => match[1])
}

/** Regex source for a path; `$param` segments match any value, e.g. `${item.id}`. */
function pathSource(path: string): string {
  return path
    .split('/')
    .map(segment =>
      segment.startsWith('$') ? '[^/\'"`]+' : segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    )
    .join('/')
}

/** Matches page.goto('<path>…') or toHaveURL('<path>…'). */
function visitPattern(path: string): RegExp {
  return new RegExp(`(?:goto|toHaveURL)\\(\\s*['"\`]${pathSource(path)}(?:['"\`?#])`)
}

test('every page route is visited by an e2e spec', () => {
  const routes = appRoutes()
  expect(routes.length).toBeGreaterThan(0)
  const untested = routes.filter(
    route => !specs.some(({ source }) => visitPattern(route).test(source))
  )
  expect(
    untested,
    `Routes without an e2e test: ${untested.join(', ')}. ` +
      `Add a spec in e2e/ that opens them, e.g. await page.goto('${untested[0]}').`
  ).toEqual([])
})

/** Every endpoint in src/lib/api-endpoints.ts; `(id) => \`/items/${id}\`` becomes '/items/$id'. */
function apiEndpoints(): string[] {
  const endpoints: string[] = []
  const collect = (value: unknown) => {
    if (typeof value === 'string') endpoints.push(value)
    else if (typeof value === 'function') {
      const params = Array.from({ length: value.length }, (_, i) => `$param${i}`)
      endpoints.push(String(value(...params)))
    } else if (value && typeof value === 'object') Object.values(value).forEach(collect)
  }
  collect(API)
  return [...new Set(endpoints)]
}

/** Matches the endpoint as the start of a string literal: '/items', '/items?size=…', `/items/${item.id}`. */
function endpointPattern(endpoint: string): RegExp {
  return new RegExp(`['"\`]${pathSource(endpoint)}(?:['"\`?#])`)
}

test('every backend endpoint the app calls is used by an e2e spec or fixture', () => {
  const endpoints = apiEndpoints()
  expect(endpoints.length).toBeGreaterThan(0)
  // fixtures.ts counts: its helpers (createItem, loginUser, …) call the endpoints for the specs.
  const sources = [...specs.map(({ source }) => source), codeOf('e2e/fixtures.ts')]
  const untested = endpoints.filter(
    endpoint => !sources.some(source => endpointPattern(endpoint).test(source))
  )
  expect(
    untested,
    `Endpoints in src/lib/api-endpoints.ts without an e2e test: ${untested.join(', ')}. ` +
      'Exercise each one from a spec (through the UI, and check the result with the api fixture), ' +
      'and add a seeding helper for a new resource in e2e/fixtures.ts.'
  ).toEqual([])
})

test('every test file in e2e/ is a spec Playwright runs', () => {
  // Playwright runs only '**/*.spec.ts'; any other test-like file would never run.
  const allowed = (file: string) =>
    file.endsWith('.spec.ts') || file === 'fixtures.ts' || file.startsWith('support/')
  const files = readdirSync(fromFrontend('e2e'), { recursive: true, encoding: 'utf8' })
    .map(file => file.split('\\').join('/'))
    .filter(file => /\.(ts|tsx|mts|cts|js|jsx|mjs|cjs)$/.test(file))
  expect(
    files.filter(file => !allowed(file)),
    'Rename these to *.spec.ts (or move helpers to e2e/support/)'
  ).toEqual([])
})

test('no mocking library is installed', () => {
  const pkg = JSON.parse(readFileSync(fromFrontend('package.json'), 'utf8'))
  const installed = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies })
  const mockLibraries =
    /^(msw|@mswjs\/.*|nock|sinon|fetch-mock|.*-fetch-mock|axios-mock-adapter|miragejs|pretender|json-server|playwright-msw|vitest|jest|@testing-library\/.*|jsdom|happy-dom)$/
  expect(
    installed.filter(name => mockLibraries.test(name)),
    'This project tests end to end against the real stack only (no mocks, no unit tests).'
  ).toEqual([])
  expect(existsSync(fromFrontend('public/mockServiceWorker.js'))).toBe(false)
})

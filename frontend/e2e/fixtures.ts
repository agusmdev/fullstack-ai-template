/**
 * Shared fixtures and helpers for every e2e spec.
 *
 *   import { test, expect } from './fixtures'
 *
 * Everything here drives the real stack that playwright.config.ts starts:
 * Postgres in Docker, the FastAPI backend (real migrations) and the frontend
 * dev server. Seed data through the backend's public HTTP API (helpers below).
 * Never mock: ESLint rejects page.route() & co. and mock libraries in e2e/.
 *
 * Adding a feature:
 *   1. Write e2e/<feature>.spec.ts that imports from './fixtures'.
 *   2. Put API helpers for the new resource here, next to createItem().
 *   3. Visit every new page from a spec, and use every new endpoint in
 *      src/lib/api-endpoints.ts from a spec or a helper here. e2e/guards.spec.ts
 *      fails for a route or an endpoint that no test uses.
 *   4. Never skip a test, and never stub the network: ESLint fails on both.
 *
 * Running: `bun run test:e2e` starts the whole stack and stops it after. To keep
 * a stack you started yourself, set E2E_REUSE=1 (see playwright.config.ts).
 *
 * Fixtures:
 *   api         APIRequestContext with baseURL = the real backend (no auth header).
 *   user        A new user registered through POST /auth/register, with its session token.
 *   authedPage  A page in its own browser context, already signed in as `user`.
 *   loginAs     (user) => a new signed-in page for any other user.
 */
import { randomUUID } from 'node:crypto'
import {
  test as base,
  expect,
  type APIRequestContext,
  type APIResponse,
  type BrowserContext,
  type Page,
  type Request,
} from '@playwright/test'
import { AUTH_TOKEN_KEY } from '../src/lib/auth'
import type { AuthSessionResponse } from '../src/types/auth'
import type { CreateItemData, Item, ItemsResponse } from '../src/types/item'
import { BACKEND_URL, FRONTEND_URL } from './support/stack'

export { expect }
export type { Locator, Page } from '@playwright/test'
export { BACKEND_URL, FRONTEND_URL }

export interface TestUser {
  email: string
  password: string
  /** Real session id from the backend. The app sends it as `Authorization: Bearer <token>`. */
  token: string
}

/** Meets the register form rules (8+ characters). */
export const PASSWORD = 'Correct-Horse-42'

/** A new address for every call, so tests never share users. Uses a real TLD: the backend rejects reserved ones. */
export function uniqueEmail(label = 'user'): string {
  return `e2e-${label}-${randomUUID()}@example.com`
}

async function expectOk(response: APIResponse, what: string): Promise<void> {
  if (!response.ok()) {
    throw new Error(`${what} failed: HTTP ${response.status()} ${await response.text()}`)
  }
}

export function authHeaders(user: Pick<TestUser, 'token'>): Record<string, string> {
  return { Authorization: `Bearer ${user.token}` }
}

// ---------------------------------------------------------------------------
// Real backend API helpers (seeding and checking state). Add new resources here.
// ---------------------------------------------------------------------------

export async function registerUser(
  api: APIRequestContext,
  email = uniqueEmail(),
  password = PASSWORD
): Promise<TestUser> {
  const response = await api.post('/auth/register', { data: { email, raw_password: password } })
  await expectOk(response, `POST /auth/register (${email})`)
  const session = (await response.json()) as AuthSessionResponse
  return { email, password, token: session.id }
}

/** Signs in through POST /auth/login and returns the new session token. */
export async function loginUser(
  api: APIRequestContext,
  email: string,
  password: string
): Promise<string> {
  const response = await api.post('/auth/login', { data: { email, password } })
  await expectOk(response, `POST /auth/login (${email})`)
  return ((await response.json()) as AuthSessionResponse).id
}

export async function createItem(
  api: APIRequestContext,
  owner: TestUser,
  data: CreateItemData
): Promise<Item> {
  const response = await api.post('/items', { data, headers: authHeaders(owner) })
  await expectOk(response, 'POST /items')
  return (await response.json()) as Item
}

/** Creates the items one after another, so the list order (created_at) follows `names`. */
export async function createItems(
  api: APIRequestContext,
  owner: TestUser,
  names: string[]
): Promise<Item[]> {
  const items: Item[] = []
  for (const name of names) items.push(await createItem(api, owner, { name }))
  return items
}

export async function listItems(api: APIRequestContext, owner: TestUser): Promise<Item[]> {
  const response = await api.get('/items?size=100', { headers: authHeaders(owner) })
  await expectOk(response, 'GET /items')
  return ((await response.json()) as ItemsResponse).items
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

/** Error toasts (sonner). Assert with toContainText(title) and the backend message. */
export function errorToast(page: Page) {
  return page.locator('[data-sonner-toast][data-type="error"]')
}

/** The value the app keeps in localStorage for the session, or null when signed out. */
export function storedToken(page: Page): Promise<string | null> {
  return page.evaluate(key => window.localStorage.getItem(key), AUTH_TOKEN_KEY)
}

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const NETWORK_CHANGED = 'net::ERR_NETWORK_CHANGED'
const MODULE_LOAD_ERROR =
  /Failed to fetch dynamically imported module|Importing a module script failed/

/**
 * Watches every page of a browser context during one test:
 *
 * - An uncaught exception in the app (React hydration errors included) fails
 *   the test. Call the returned function after the test to check.
 * - Host network changes are survived. When Docker on the same machine starts
 *   containers or networks, Chromium can abort in-flight requests with
 *   net::ERR_NETWORK_CHANGED, even to 127.0.0.1. If that breaks the loading of
 *   the app's modules, the page never hydrates. That is the machine, not the
 *   app: such a page is reloaded and its module-load error is ignored. Any other
 *   failure (an aborted API call included) still fails the test.
 */
function watchContext(context: BrowserContext): () => void {
  const errors: string[] = []
  const hitByNetworkChange = new WeakSet<Page>()
  const reloads = new WeakMap<Page, number>()
  // Top-level document requests in flight, per page.
  const loading = new Map<Page, Set<Request>>()

  const pageLoad = (request: Request) =>
    request.isNavigationRequest() && request.frame() === request.frame().page().mainFrame()

  async function reload(page: Page) {
    // The reload itself can be aborted by the next network change: try again.
    while (!page.isClosed() && (reloads.get(page) ?? 0) < 5) {
      // The test is already loading another page, which replaces the broken one.
      if (loading.get(page)?.size) return
      reloads.set(page, (reloads.get(page) ?? 0) + 1)
      const reloaded = await page.reload().then(
        () => true,
        () => false
      )
      if (reloaded) return
      await new Promise(resolve => setTimeout(resolve, 250))
    }
  }

  context.on('request', request => {
    if (!pageLoad(request)) return
    const page = request.frame().page()
    loading.set(page, (loading.get(page) ?? new Set()).add(request))
  })
  const loaded = (request: Request) => {
    if (pageLoad(request)) loading.get(request.frame().page())?.delete(request)
  }
  context.on('requestfinished', loaded)
  context.on('requestfailed', request => {
    loaded(request)
    if (request.failure()?.errorText === NETWORK_CHANGED) {
      hitByNetworkChange.add(request.frame().page())
    }
  })

  context.on('weberror', webError => {
    const error = webError.error()
    const page = webError.page()
    if (page && hitByNetworkChange.has(page) && MODULE_LOAD_ERROR.test(error.message)) {
      void reload(page)
      return
    }
    errors.push(`${page?.url() ?? ''}\n${error.stack || `${error.name}: ${error.message}`}`)
  })

  return () => {
    if (errors.length > 0) throw new Error(`Uncaught errors in the app:\n\n${errors.join('\n\n')}`)
  }
}

interface Fixtures {
  api: APIRequestContext
  user: TestUser
  loginAs: (user: TestUser) => Promise<Page>
  authedPage: Page
}

export const test = base.extend<Fixtures>({
  context: async ({ context }, use) => {
    const assertNoPageErrors = watchContext(context)
    await use(context)
    assertNoPageErrors()
  },

  api: async ({ playwright }, use) => {
    const api = await playwright.request.newContext({ baseURL: BACKEND_URL })
    await use(api)
    await api.dispose()
  },

  user: async ({ api }, use) => {
    await use(await registerUser(api))
  },

  loginAs: async ({ browser }, use) => {
    const opened: { context: BrowserContext; assertNoPageErrors: () => void }[] = []
    await use(async user => {
      // The same thing a real sign-in leaves behind: the session token in localStorage.
      const context = await browser.newContext({
        storageState: {
          cookies: [],
          origins: [
            { origin: FRONTEND_URL, localStorage: [{ name: AUTH_TOKEN_KEY, value: user.token }] },
          ],
        },
      })
      opened.push({ context, assertNoPageErrors: watchContext(context) })
      return context.newPage()
    })
    for (const { context } of opened) await context.close()
    for (const { assertNoPageErrors } of opened) assertNoPageErrors()
  },

  authedPage: async ({ loginAs, user }, use) => {
    await use(await loginAs(user))
  },
})

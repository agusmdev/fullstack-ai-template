import { defineConfig, devices } from '@playwright/test'
import {
  BACKEND_PORT,
  BACKEND_URL,
  DB_CONTAINER,
  DB_PORT,
  DB_URL,
  FRONTEND_PORT,
  FRONTEND_URL,
  composePostgresImage,
} from './e2e/support/stack'

/**
 * End-to-end tests against the real stack: Postgres in Docker, the FastAPI
 * backend with real migrations, and the Vite dev server. No mocks.
 *
 * `bun run test:e2e` starts all three (webServer below), runs every .spec.ts
 * file in e2e/ and its subfolders, and stops them again. Specs import
 * { test, expect } from './fixtures'.
 */
const isCI = !!process.env.CI
// Reuse a stack that is already running only when asked (E2E_REUSE=1, never in
// CI). Without it, a server on the e2e ports is an error: it may belong to
// another checkout, with other code and another database.
const reuse = !isCI && !!process.env.E2E_REUSE

// Each stack piece watches this PID and stops itself if the runner is killed.
const supervision = { E2E_RUNNER_PID: String(process.pid) }
const stopGracefully = { signal: 'SIGTERM', timeout: 15_000 } as const

export default defineConfig({
  testDir: './e2e',
  // Only .spec.ts files run: ESLint checks those for mocks (eslint.config.js).
  testMatch: '**/*.spec.ts',
  fullyParallel: true,
  forbidOnly: true,
  // A flaky e2e test is a bug to fix, not to retry.
  retries: 0,
  workers: isCI ? 2 : undefined,
  reporter: isCI ? [['list'], ['html', { open: 'never' }]] : [['list']],
  // The dev server compiles each module on its first request: the first page
  // load of a run can take a few seconds to hydrate on a slow CI machine.
  expect: { timeout: 10_000 },
  use: {
    baseURL: FRONTEND_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Started in order; each one must be ready before the next starts.
  webServer: [
    {
      name: 'db',
      command: 'bash e2e/support/stack.sh db',
      env: {
        ...supervision,
        E2E_REUSE: reuse ? '1' : '',
        E2E_DB_CONTAINER: DB_CONTAINER,
        E2E_DB_PORT: String(DB_PORT),
        E2E_BACKEND_PORT: String(BACKEND_PORT), // to tell whether a running backend will be reused
        E2E_DB_IMAGE: composePostgresImage(),
      },
      wait: { stdout: /e2e db ready/ },
      stdout: 'pipe',
      timeout: 120_000,
      gracefulShutdown: stopGracefully,
    },
    {
      name: 'backend',
      command: 'bash e2e/support/stack.sh backend',
      url: `${BACKEND_URL}/health`,
      env: {
        ...supervision,
        E2E_BACKEND_PORT: String(BACKEND_PORT),
        // Explicit values, so a developer's backend/.env cannot leak into the run.
        DB_URL,
        DB_POOL_PRE_PING: 'true',
        FRONTEND_URL,
        ENVIRONMENT: 'local',
        LOG_LEVEL: 'ERROR', // 5xx and crashes only; 4xx are expected in these tests
        SENTRY_DSN: '',
        GOOGLE_CLIENT_ID: '',
        GOOGLE_CLIENT_SECRET: '',
      },
      reuseExistingServer: reuse,
      timeout: 180_000,
      gracefulShutdown: stopGracefully,
    },
    {
      name: 'frontend',
      command: 'bash e2e/support/stack.sh frontend',
      url: FRONTEND_URL,
      stdout: 'pipe', // Vite's own messages (e.g. dependency re-bundling) explain odd reloads
      env: {
        ...supervision,
        E2E_FRONTEND_PORT: String(FRONTEND_PORT),
        VITE_API_BASE_URL: BACKEND_URL,
      },
      reuseExistingServer: reuse,
      timeout: 120_000,
      gracefulShutdown: stopGracefully,
    },
  ],
})

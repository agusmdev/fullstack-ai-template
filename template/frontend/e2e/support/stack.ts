/**
 * Where the e2e stack runs. playwright.config.ts starts it, fixtures.ts talks to it.
 *
 * The ports differ from the dev stack (db 5432, backend 9095, frontend 3000), so
 * the suite never touches a running dev environment. Set E2E_DB_PORT,
 * E2E_BACKEND_PORT or E2E_FRONTEND_PORT to run two checkouts side by side.
 * The e2e frontend does not start the TanStack devtools event bus (fixed port
 * 42069, see vite.config.ts), so no other port is shared.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

function portFromEnv(name: string, fallback: number): number {
  const value = Number(process.env[name] ?? fallback)
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${name} must be a port number`)
  return value
}

export const DB_PORT = portFromEnv('E2E_DB_PORT', 55432)
export const BACKEND_PORT = portFromEnv('E2E_BACKEND_PORT', 59095)
export const FRONTEND_PORT = portFromEnv('E2E_FRONTEND_PORT', 53000)

// 127.0.0.1 everywhere: "localhost" can resolve to ::1 first, and the browser
// origin must match the backend's CORS setting (FRONTEND_URL) exactly.
export const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`
export const FRONTEND_URL = `http://127.0.0.1:${FRONTEND_PORT}`

export const DB_CONTAINER = `e2e-postgres-${DB_PORT}`
export const DB_URL = `postgresql://app:app@127.0.0.1:${DB_PORT}/app`

/** Same Postgres image as the `db` service in ../docker-compose.yml, so e2e runs on the real version. */
export function composePostgresImage(): string {
  if (process.env.E2E_DB_IMAGE) return process.env.E2E_DB_IMAGE
  const composeFile = fileURLToPath(new URL('../../../docker-compose.yml', import.meta.url))
  const compose = readFileSync(composeFile, 'utf8')
  const image = /^ {2}db:\s*\n(?: {4}.*\n)*? {4}image:\s*(\S+)/m.exec(compose)?.[1]
  if (!image) {
    throw new Error(`No image for the "db" service in ${composeFile}. Set E2E_DB_IMAGE.`)
  }
  return image
}

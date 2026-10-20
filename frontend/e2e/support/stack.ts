/**
 * Where the e2e stack runs. playwright.config.ts starts it, fixtures.ts talks to it.
 *
 * Each run picks free ports, so it never touches a running dev environment or
 * another checkout's run. Set E2E_DB_PORT, E2E_BACKEND_PORT or
 * E2E_FRONTEND_PORT to choose them. With E2E_REUSE=1 the ports are fixed
 * (55432, 59095, 53000), so a second run finds the stack the first one left.
 * The e2e frontend does not start the TanStack devtools event bus (fixed port
 * 42069, see vite.config.ts), so no other port is shared.
 */
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const PORTS = { E2E_DB_PORT: 55432, E2E_BACKEND_PORT: 59095, E2E_FRONTEND_PORT: 53000 }
type PortName = keyof typeof PORTS

/** Binds `count` ports at once (so they differ), then frees them. Synchronous: the config cannot await. */
function freePorts(count: number): number[] {
  const script = `
    const net = require('node:net')
    const servers = Array.from({ length: ${count} }, () => net.createServer())
    Promise.all(servers.map((s) => new Promise((ok) => s.listen(0, '127.0.0.1', ok)))).then(() => {
      process.stdout.write(servers.map((s) => s.address().port).join(','))
      servers.forEach((s) => s.close())
    })`
  return execFileSync(process.execPath, ['-e', script], { encoding: 'utf8' }).split(',').map(Number)
}

// The runner loads this file first and writes the chosen ports to process.env.
// Its worker processes inherit that env, so every process sees the same ports.
const unset = (Object.keys(PORTS) as PortName[]).filter(name => !process.env[name])
const picked =
  process.env.E2E_REUSE || unset.length === 0
    ? unset.map(name => PORTS[name])
    : freePorts(unset.length)
unset.forEach((name, i) => (process.env[name] = String(picked[i])))

function portFromEnv(name: PortName): number {
  const value = Number(process.env[name])
  if (!Number.isInteger(value) || value <= 0) throw new Error(`${name} must be a port number`)
  return value
}

export const DB_PORT = portFromEnv('E2E_DB_PORT')
export const BACKEND_PORT = portFromEnv('E2E_BACKEND_PORT')
export const FRONTEND_PORT = portFromEnv('E2E_FRONTEND_PORT')

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

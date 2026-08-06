import { describe, it, expect } from 'vitest'
import { getRouter } from './router'
import { routeTree } from './routeTree.gen'

describe('getRouter', () => {
  it('returns a router instance built from the generated route tree', () => {
    const router = getRouter()
    expect(router).toBeDefined()
    // TanStack Router exposes the resolved routes on the instance.
    expect(router.routesById).toBeDefined()
  })

  it('returns a fresh router on each call', () => {
    const a = getRouter()
    const b = getRouter()
    expect(a).not.toBe(b)
  })

  it('registers the root, index, login, register, authed, and team-scoped routes', () => {
    const router = getRouter()
    const ids = Object.keys(router.routesById)
    expect(ids).toEqual(
      expect.arrayContaining([
        '__root__',
        '/',
        '/login',
        '/register',
        '/_authed',
        '/_authed/workspace',
        '/_authed/$team/',
        '/_authed/$team/issues',
        '/_authed/$team/board',
        '/_authed/$team/projects',
        '/_authed/$team/cycles',
        '/_authed/$team/views',
        '/_authed/$team/settings',
      ]),
    )
  })
})

describe('routeTree (generated module)', () => {
  it('exports a non-null route tree derived from the file routes', () => {
    // The generator builds the tree from src/routes/*; importing it here is the
    // smoke test that the generated file is valid and wireable to a router.
    expect(routeTree).toBeDefined()
    const router = getRouter()
    expect(Object.keys(router.routesById)).toEqual(
      expect.arrayContaining([
        '/',
        '/login',
        '/register',
        '/_authed/workspace',
        '/_authed/$team/issues',
        '/_authed/$team/board',
        '/_authed/$team/projects',
        '/_authed/$team/cycles',
        '/_authed/$team/views',
        '/_authed/$team/settings',
      ]),
    )
  })
})

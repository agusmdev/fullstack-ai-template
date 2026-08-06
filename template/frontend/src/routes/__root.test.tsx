import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { Route } from './__root'

// __root wires providers, devtools, web-vitals, and the document shell around
// the router. A full integration render requires a complete RouterProvider and
// pulls in lazy devtools bundles, which makes a render-based test fragile and
// low-signal. Instead these tests pin the route's exported contract (head
// metadata + shell component identity), which is the module's real responsibility.
vi.mock('@/lib/web-vitals', () => ({ initWebVitals: vi.fn() }))

describe('__root route', () => {
  // The root route's options are a complex TanStack Router union; narrow to the
  // shape we care about for these contract assertions.
  const options = Route.options as unknown as {
    head: () => { meta: unknown[]; links: unknown[] }
    shellComponent: React.FC
  }

  it('exports a route with a head() and a shellComponent', () => {
    expect(typeof options.head).toBe('function')
    expect(typeof options.shellComponent).toBe('function')
  })

  it('head() declares charset, viewport, and the document title', () => {
    const { meta } = options.head()
    expect(meta).toEqual(
      expect.arrayContaining([
        { charSet: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { title: 'Manta' },
      ]),
    )
  })

  it('head() links the app stylesheet', () => {
    const { links } = options.head()
    expect(links).toEqual(expect.arrayContaining([expect.objectContaining({ rel: 'stylesheet' })]))
  })

  it('the shellComponent is the RootDocument (a React function component)', () => {
    const RootDocument = options.shellComponent
    expect(typeof RootDocument).toBe('function')
    expect(RootDocument.name).toBe('RootDocument')
  })
})

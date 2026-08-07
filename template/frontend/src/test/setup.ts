// Vitest setup file for React Testing Library.
//
// This file runs before each test file and sets up the necessary globals.

import React from 'react'
import { cleanup } from '@testing-library/react'
import { afterEach, vi, afterAll } from 'vitest'
import '@testing-library/jest-dom/vitest'

// jsdom does not implement ResizeObserver, but `cmdk` (used by the command
// palette) and some Radix primitives rely on it at mount. Provide a no-op
// polyfill so components render in the test environment.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
vi.stubGlobal('ResizeObserver', ResizeObserverStub)

// jsdom also omits Element.scrollIntoView, which cmdk calls to keep the
// active item in view. Provide a no-op so palette interactions work in tests.
Element.prototype.scrollIntoView = () => {}

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Teardown to prevent Vite hanging
afterAll(() => {
  cleanup()
})

// Mock TanStack Router's Link component
vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router')
  return {
    ...actual,
    Link: ({ children, to, ...props }: { children: React.ReactNode; to: string; [key: string]: unknown }) =>
      React.createElement('a', { href: to, ...props }, children),
  }
})

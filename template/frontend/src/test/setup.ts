// Vitest setup file for React Testing Library.
//
// This file runs before each test file and sets up the necessary globals.

import React from 'react'
import { cleanup } from '@testing-library/react'
import { afterEach, vi, afterAll } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

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

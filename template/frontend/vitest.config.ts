/// <reference types="vitest/globals" />

import { defineConfig } from 'vitest/config'
import viteReact from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'url'

export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // Cast: vitest 3.0.5 bundles an older vite than the project's vite 7.1.7,
  // causing PluginOption type mismatch. Runtime is unaffected.
  plugins: [viteReact() as never],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['**/*.test.{ts,tsx}'],
    poolOptions: {
      threads: {
        singleThread: true,
      },
    },
    teardownTimeout: 1000,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/**/*.d.ts',
        'src/test/**',
        'src/routeTree.gen.ts',
        'src/**/types/**',
      ],
      thresholds: {
        lines: 40,
        functions: 40,
        branches: 30,
        statements: 40,
      },
    },
  },
})

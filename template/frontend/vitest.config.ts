import { defineConfig } from 'vitest/config'
import { fileURLToPath, URL } from 'url'

// Dedicated vitest config. Vitest selects this file automatically and it takes
// precedence over vite.config.ts. Uses `defineConfig` from `vitest/config` so
// the `test` property typechecks (vite's own UserConfig has no `test`).
//
// No `@vitejs/plugin-react` here: vitest 3.0.5 ships a nested copy of vite whose
// PluginOption type is incompatible with the vite-7-typed plugin, which would
// break `bunx tsc --noEmit`. Vitest transforms JSX via esbuild using tsconfig's
// `jsx: "react-jsx"`, so the React plugin isn't required for tests. The `@`
// alias is handled by `resolve.alias` below.
export default defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
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
  },
})

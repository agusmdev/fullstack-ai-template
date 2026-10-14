import { defineConfig } from 'vite'
import { devtools } from '@tanstack/devtools-vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import viteTsConfigPaths from 'vite-tsconfig-paths'
import { nitro } from 'nitro/vite'
import tailwindcss from '@tailwindcss/vite'

const config = defineConfig({
  plugins: [
    // The devtools server event bus always listens on port 42069. The e2e stack
    // (E2E_RUNNER_PID is set by playwright.config.ts) turns it off, so a test
    // run can start while `bun run dev` or another checkout's e2e run is up.
    devtools({ eventBusConfig: { enabled: !process.env.E2E_RUNNER_PID } }),
    nitro(),
    // this is the plugin that enables path aliases
    viteTsConfigPaths({
      projects: ['./tsconfig.json'],
    }),

    tanstackStart(),
    viteReact(),
    tailwindcss(),
  ],
  optimizeDeps: {
    // TanStack Start has no index.html, so Vite finds dependencies only when a
    // page first imports them, then re-bundles and reloads the page (and old
    // module requests fail with "504 Outdated Optimize Dep"). Scanning all app
    // sources at startup bundles everything up front.
    entries: ['src/**/*.{ts,tsx}'],
  },
})

export default config

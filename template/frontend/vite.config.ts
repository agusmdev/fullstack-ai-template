import { defineConfig } from 'vite'
import { devtools } from '@tanstack/devtools-vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import viteTsConfigPaths from 'vite-tsconfig-paths'
import { fileURLToPath, URL } from 'url'
import { nitro } from 'nitro/vite'
import tailwindcss from '@tailwindcss/vite'

const config = defineConfig({
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  plugins: [
    devtools(),
    nitro(),
    // this is the plugin that enables path aliases
    viteTsConfigPaths({
      projects: ['./tsconfig.json'],
    }),

    tanstackStart(),
    viteReact(),
    tailwindcss(),
  ],
  // Vitest configuration lives in vitest.config.ts (vitest selects it
  // automatically and takes precedence over this file). Keeping the test block
  // out of here avoids a tsc drift: vite's UserConfig has no `test` property,
  // and the vitest/config type reference cannot augment it because vitest 3.0
  // ships a nested copy of vite whose UserConfig differs from vite 7's.
})

export default config

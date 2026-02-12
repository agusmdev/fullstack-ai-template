---
name: tanstack-start-project-setup
description: Initialize a TanStack Start (SSR) project with Vite, server functions, React Query, and proper configuration.
---

# TanStack Start Project Setup

## Overview

This skill covers initializing a new TanStack Start project with bun package manager. TanStack Start is a full-stack React framework with integrated routing, server-side rendering, and data fetching capabilities.

## Step 1: Create Project with CLI

The easiest way to initialize a TanStack Start project is using the official CLI:

```bash
bunx create @tanstack/start@latest
```

Or manually with npm:

```bash
npm create @tanstack/start@latest
```

The CLI will prompt for:
- Project name
- Optional add-ons (Tailwind CSS, ESLint, Shadcn, TanStack Query, etc.)

## Step 2: Navigate to Project

```bash
cd your-project-name
```

## Step 3: Install Dependencies

If you created the project with the CLI, install dependencies:

```bash
bun install
```

For Bun deployment, upgrade React to version 19+:

```bash
bun install react@19 react-dom@19
```

## Step 4: Create package.json (if building from scratch)

```json
{
  "name": "your-project-name",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "start": "node .output/server/index.mjs"
  },
  "dependencies": {
    "@tanstack/react-router": "^1.84.0",
    "@tanstack/react-start": "^1.84.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "vite": "^6.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.10.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.7.2",
    "vite-tsconfig-paths": "^5.1.4"
  }
}
```

## Step 5: Create tsconfig.json

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "moduleResolution": "Bundler",
    "module": "ESNext",
    "target": "ES2022",
    "skipLibCheck": true,
    "strictNullChecks": true,
    "baseUrl": ".",
    "paths": {
      "~/*": ["./src/*"]
    }
  }
}
```

## Step 6: Create vite.config.ts

Basic configuration:

```typescript
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  server: {
    port: 3000,
  },
  plugins: [
    tsconfigPaths(),
    tanstackStart(),
    // React's vite plugin must come after start's vite plugin
    viteReact(),
  ],
})
```

For Bun deployment, add Nitro preset:

```typescript
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { nitro } from 'nitro/vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    tanstackStart(),
    nitro({ preset: 'bun' }),
    viteReact(),
  ],
})
```

With custom routes directory (App Router style):

```typescript
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  server: {
    port: 3000,
  },
  plugins: [
    tsconfigPaths(),
    tanstackStart({
      srcDirectory: 'src',
      router: {
        routesDirectory: 'app',
      },
    }),
    viteReact(),
  ],
})
```

## Step 7: Create Directory Structure

```bash
mkdir -p src/{routes,types}
mkdir -p public
touch src/router.tsx
```

Standard project structure:

```
your-project-name/
├── src/
│   ├── routes/            # File-based routing
│   │   └── __root.tsx     # Root layout
│   ├── types/             # TypeScript types
│   ├── router.tsx         # Router configuration
│   └── routeTree.gen.ts   # Generated route tree (auto-generated)
├── public/                # Static assets
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
├── package.json           # Dependencies and scripts
└── .gitignore
```

## Step 8: Create Root Route

Create `src/routes/__root.tsx`:

```tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <html>
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>TanStack Start App</title>
      </head>
      <body>
        <Outlet />
      </body>
    </html>
  ),
})
```

## Step 9: Create Router Configuration

Create `src/router.tsx`:

```tsx
import { createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
```

## Step 10: Start Development Server

```bash
bun run dev
```

The application will be available at `http://localhost:3000`.

## Verification

After setup, verify:
1. Development server starts without errors
2. Navigate to `http://localhost:3000` and see the TanStack Start welcome page
3. TypeScript compilation works: `bun run build`
4. Route tree is auto-generated in `src/routeTree.gen.ts`

## Notes

- TanStack Start uses file-based routing in the `src/routes/` directory
- The route tree is automatically generated by Vite plugin
- Always use `bunx` or `bun run` for commands
- For Bun deployment, ensure React 19+ is installed
- Server functions can be defined with `createServerFn`
- TanStack Query integration is optional but recommended

## Next Steps

After project setup:
- Add routes in `src/routes/` directory
- Configure TanStack Query (see `tanstack-react-query-setup` skill)
- Set up Tailwind CSS and shadcn/ui (see `tanstack-shadcn-setup` skill)
- Add server functions for data fetching (see `tanstack-start-server-functions` skill)

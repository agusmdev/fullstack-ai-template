---
name: tanstack-start-client-only
description: Configure TanStack Start in client-only mode (defaultSsr=false) for SPA-like behavior without server-side rendering.
---

# TanStack Start Client-Only Mode

## Overview

This skill covers configuring TanStack Start to run in client-only mode by disabling server-side rendering (SSR). This is useful when you want SPA-like behavior or when your application doesn't benefit from SSR.

## When to Use Client-Only Mode

Use client-only mode when:
- Building a traditional SPA that doesn't need SEO
- Your app is behind authentication (private dashboards, admin panels)
- You want faster development iteration without SSR complexity
- Your backend is a separate API service
- You don't need initial page load performance optimizations

## Step 1: Configure Router with defaultSsr=false

Modify your `src/router.tsx` to disable SSR:

```typescript
import { createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export const router = createRouter({
  routeTree,
  defaultSsr: false, // Disable server-side rendering globally
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
```

## Step 2: Per-Route SSR Control (Optional)

You can also control SSR on a per-route basis by setting `ssr: false` in individual route definitions:

```typescript
// src/routes/dashboard.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard')({
  // Disable SSR for this specific route
  ssr: false,
  component: DashboardComponent,
})

function DashboardComponent() {
  return <div>Dashboard (Client-Only)</div>
}
```

## Step 3: Update Root Route for Client-Only

Ensure your `src/routes/__root.tsx` is properly configured for client-only rendering:

```tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <html>
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>TanStack Start App (Client-Only)</title>
      </head>
      <body>
        <div id="root">
          <Outlet />
        </div>
      </body>
    </html>
  ),
})
```

## Step 4: Handle Browser-Only APIs

In client-only mode, you can safely use browser APIs without checking for SSR:

```typescript
import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/example')({
  component: ExampleComponent,
})

function ExampleComponent() {
  const [data, setData] = useState(null)

  useEffect(() => {
    // Browser APIs work directly since there's no SSR
    const stored = localStorage.getItem('data')
    if (stored) {
      setData(JSON.parse(stored))
    }

    // Window object is available
    console.log('Window size:', window.innerWidth, window.innerHeight)
  }, [])

  return <div>Example Component</div>
}
```

## Step 5: Configure Vite for Client-Only (Optional)

For pure client-only builds, you can simplify your `vite.config.ts`:

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
      // Client-only mode configuration
      ssr: false, // Disable SSR at build level
    }),
    viteReact(),
  ],
})
```

## Step 6: Environment Variables for Client-Only

Create `.env` for client-side environment variables:

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=My TanStack App
```

Access them in your components:

```typescript
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
const appName = import.meta.env.VITE_APP_NAME
```

**Note:** In client-only mode, all `VITE_*` variables are exposed to the client bundle. Never store secrets here.

## Step 7: Build and Deploy

Build your client-only application:

```bash
bun run build
```

This creates a static bundle in `.output/` that can be deployed to:
- Static hosting (Vercel, Netlify, Cloudflare Pages)
- CDN
- Traditional web servers (nginx, Apache)

## Comparison: SSR vs Client-Only

| Feature | SSR (default) | Client-Only (defaultSsr=false) |
|---------|--------------|-------------------------------|
| Initial page load | Fully rendered HTML | Empty HTML shell |
| SEO | Excellent | Limited (depends on crawlers) |
| Time to First Byte (TTFB) | Slower (server processing) | Fast (static HTML) |
| JavaScript bundle | Hydration required | Direct execution |
| Server-side APIs | Available via server functions | Must use external API |
| Browser APIs | Require checks | Always available |
| Deployment | Node.js server required | Static hosting works |

## Best Practices

1. **Use client-only for authenticated apps**: Dashboards, admin panels, and internal tools benefit from simpler client-only architecture.

2. **Combine both modes**: Use SSR for marketing pages (`/`, `/pricing`, `/blog`) and client-only for app routes (`/dashboard/*`, `/settings/*`):

```typescript
// src/routes/__root.tsx
export const Route = createRootRoute({
  component: RootComponent,
})

// src/routes/index.tsx (SSR - default)
export const Route = createFileRoute('/')({
  component: HomePage,
})

// src/routes/dashboard.tsx (Client-only)
export const Route = createFileRoute('/dashboard')({
  ssr: false, // Disable SSR for dashboard
  component: Dashboard,
})
```

3. **Optimize bundle size**: In client-only mode, the entire app loads on first visit. Use code splitting:

```typescript
import { lazy } from 'react'

const HeavyComponent = lazy(() => import('./HeavyComponent'))

function Dashboard() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <HeavyComponent />
      </Suspense>
    </div>
  )
}
```

4. **Handle loading states**: Without SSR, users see blank screens until JavaScript loads. Add loading indicators:

```tsx
// src/routes/__root.tsx
export const Route = createRootRoute({
  component: () => (
    <html>
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>TanStack Start App</title>
        <style>{`
          .app-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            font-family: system-ui;
          }
        `}</style>
      </head>
      <body>
        <div id="root">
          <div className="app-loading">Loading application...</div>
          <Outlet />
        </div>
      </body>
    </html>
  ),
})
```

## Verification

After configuring client-only mode:

1. Start the development server:
```bash
bun run dev
```

2. Open browser DevTools → Network tab
3. Check the initial HTML response - it should contain minimal HTML without rendered content
4. Verify JavaScript executes and renders the application
5. Test that browser APIs work without SSR checks

## Troubleshooting

### Issue: "window is not defined" errors

**Cause:** Accidentally running SSR code when `defaultSsr: false` isn't set.

**Solution:** Ensure `defaultSsr: false` in router configuration:
```typescript
export const router = createRouter({
  routeTree,
  defaultSsr: false,
})
```

### Issue: Blank page on load

**Cause:** JavaScript bundle failed to load or execute.

**Solution:** Check browser console for errors and verify bundle path in network tab.

### Issue: Hydration warnings

**Cause:** Mixing SSR and client-only rendering.

**Solution:** Be consistent - either use `defaultSsr: false` globally or manage per-route carefully.

## Notes

- Client-only mode simplifies development by removing SSR complexity
- Perfect for apps that don't need SEO or fast initial loads
- Can be combined with SSR on a per-route basis for hybrid applications
- All TanStack Router features (nested routes, loaders, search params) work in client-only mode
- React Query works identically in both SSR and client-only modes

## Next Steps

After configuring client-only mode:
- Set up TanStack Query for data fetching (see `tanstack-react-query-setup` skill)
- Add authentication guards (see `tanstack-client-auth` skill)
- Configure API client layer (see `tanstack-client-api-layer` skill)
- Set up Tailwind CSS and shadcn/ui (see `tanstack-shadcn-setup` skill)

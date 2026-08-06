import React, { useEffect, useState } from 'react'
import { HeadContent, Outlet, Scripts, createRootRoute } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function lazyDev<P = any>(factory: () => Promise<React.ComponentType<P>>): React.ComponentType<P> {
  return import.meta.env.DEV
    ? React.lazy(() => factory().then(c => ({ default: c })))
    : (() => null) as React.ComponentType<P>
}

const ReactQueryDevtools = lazyDev(
  () => import('@tanstack/react-query-devtools').then(m => m.ReactQueryDevtools)
)
const TanStackDevtools = lazyDev(
  () => import('@tanstack/react-devtools').then(m => m.TanStackDevtools)
)
const TanStackRouterDevtoolsPanel = lazyDev(
  () => import('@tanstack/react-router-devtools').then(m => m.TanStackRouterDevtoolsPanel)
)

import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import { initWebVitals } from '@/lib/web-vitals'
import { THEME_STORAGE_KEY, applyTheme, getStoredTheme } from '@/lib/theme'

import appCss from '@/styles/app.css?url'

/**
 * Inline script injected into <head> that resolves the persisted theme
 * (light/dark/system) from localStorage and toggles the `.dark` class on <html>
 * BEFORE React renders. This prevents a flash of the wrong theme on first paint
 * and across reload/logout-login (the preference is independent of auth state).
 */
const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem(${JSON.stringify(
  THEME_STORAGE_KEY
)})||'system';var d=t==='dark'||(t==='system'&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);}catch(e){}})();`

export const Route = createRootRoute({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        title: 'Linear',
      },
    ],
    links: [
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),

  shellComponent: RootDocument,
})

function RootDocument() {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  }))

  useEffect(() => {
    initWebVitals()
    // Re-apply the persisted theme after mount: the before-paint init script
    // prevents the initial flash, but React hydration may reconcile the <html>
    // class. This restores it immediately so no perceptible flash occurs.
    applyTheme(getStoredTheme())
  }, [])

  return (
    // suppressHydrationWarning: the theme init script mutates <html class>
    // before React hydrates, which would otherwise warn about a mismatch.
    <html lang="en" suppressHydrationWarning>
      <head>
        <HeadContent />
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          <AuthProvider queryClient={queryClient}>
            <ErrorBoundary>
              <Outlet />
            </ErrorBoundary>
            <Toaster />
            <React.Suspense>
              <ReactQueryDevtools initialIsOpen={false} />
              <TanStackDevtools
                config={{
                  position: 'bottom-right',
                }}
                plugins={[
                  {
                    name: 'Tanstack Router',
                    render: <TanStackRouterDevtoolsPanel />,
                  },
                ]}
              />
            </React.Suspense>
          </AuthProvider>
        </QueryClientProvider>
        <Scripts />
      </body>
    </html>
  )
}

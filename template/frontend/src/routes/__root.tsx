import React, { useEffect } from 'react'
import { HeadContent, Scripts, createRootRoute } from '@tanstack/react-router'
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

import { Layout } from '@/components/Layout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import { initWebVitals } from '@/lib/web-vitals'

import appCss from '@/styles/app.css?url'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

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
        title: 'TanStack Start Starter',
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
  useEffect(() => {
    initWebVitals()
  }, [])

  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          <AuthProvider queryClient={queryClient}>
            <ErrorBoundary>
              <Layout />
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

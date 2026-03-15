import React from 'react'
import { HeadContent, Scripts, createRootRoute } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const ReactQueryDevtools = import.meta.env.DEV
  ? React.lazy(() =>
      import('@tanstack/react-query-devtools').then(m => ({ default: m.ReactQueryDevtools }))
    )
  : () => null

const TanStackDevtools = import.meta.env.DEV
  ? React.lazy(() =>
      import('@tanstack/react-devtools').then(m => ({ default: m.TanStackDevtools }))
    )
  : () => null

const TanStackRouterDevtoolsPanel = import.meta.env.DEV
  ? React.lazy(() =>
      import('@tanstack/react-router-devtools').then(m => ({ default: m.TanStackRouterDevtoolsPanel }))
    )
  : () => null

import Layout from '../components/Layout'
import { ErrorBoundary } from '../components/ErrorBoundary'
import { Toaster } from '../components/ui/sonner'
import { AuthProvider } from '../contexts/AuthContext'
import { initWebVitals } from '../lib/web-vitals'

import appCss from '../styles/app.css?url'

// Initialize Web Vitals tracking
if (typeof window !== 'undefined') {
  initWebVitals()
}

// Create a QueryClient instance
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

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <QueryClientProvider client={queryClient}>
          <AuthProvider queryClient={queryClient}>
            <ErrorBoundary>
              <Layout>
                {children}
              </Layout>
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

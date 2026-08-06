import { Skeleton } from '@/components/ui/skeleton'

/**
 * Neutral, auth-state-independent loading shell rendered during SSR and the
 * very first client paint (before hydration completes).
 *
 * It contains no browser-only state — no localStorage reads, no data queries,
 * no `window`/`matchMedia` access — so the server-rendered HTML and the first
 * client render are byte-identical. This is what eliminates the React
 * hydration-mismatch warning on authenticated SSR load: the server cannot see
 * the localStorage auth token, so any auth-dependent rendering would diverge.
 * Once hydration confirms the client environment, the real `<AppShell>` takes
 * over (see the `_authed` layout's hydration gate).
 */
export function AppShellSkeleton() {
  return (
    <div
      className="flex h-screen overflow-hidden bg-background text-foreground"
      role="status"
      aria-busy="true"
    >
      {/* Sidebar rail placeholder (mirrors AppShell dimensions) */}
      <div
        className="hidden w-60 shrink-0 border-r border-border bg-card md:flex"
        aria-hidden="true"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar placeholder */}
        <div className="flex h-12 items-center border-b border-border bg-background px-4">
          <Skeleton className="h-6 w-40" />
        </div>
        {/* Main content placeholder */}
        <main className="flex-1 overflow-auto p-6">
          <Skeleton className="h-4 w-32" />
        </main>
      </div>
      <span className="sr-only">Loading workspace…</span>
    </div>
  )
}

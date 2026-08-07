import { useEffect, useState } from 'react'

/**
 * Returns `false` during server-side rendering and the very first client
 * render, then `true` once the component has mounted (i.e. after React has
 * hydrated the server-rendered HTML).
 *
 * Use this to gate rendering that depends on browser-only state (localStorage,
 * `window`, media queries) so the server output and the first client paint are
 * byte-identical. This is the standard pattern for eliminating React
 * hydration-mismatch warnings caused by client/server state divergence — for
 * example, an auth token that lives in localStorage and is invisible to SSR.
 */
export function useIsHydrated(): boolean {
  const [isHydrated, setIsHydrated] = useState(false)
  useEffect(() => {
    setIsHydrated(true)
  }, [])
  return isHydrated
}

import { useSyncExternalStore } from 'react'

const subscribe = () => () => {}

/**
 * False on the server and during hydration, true once React runs in the browser.
 * Server-rendered forms stay disabled until then: before hydration a click on
 * "Submit" would do a native form POST, and typed text could be lost.
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false
  )
}

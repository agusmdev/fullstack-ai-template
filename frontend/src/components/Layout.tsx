import { Outlet } from '@tanstack/react-router'
import { Navigation } from './Navigation'

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navigation />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}

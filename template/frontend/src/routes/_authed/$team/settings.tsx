import { createFileRoute } from '@tanstack/react-router'
import { ThemeToggle } from '@/components/ThemeToggle'
import { useUser } from '@/hooks/useUser'

/**
 * Settings view — profile + theme preferences.
 *
 * Reachable from the topbar user menu (VAL-CROSS-005). The theme toggle here
 * is the same control as in the topbar; it persists across reload and
 * logout/login.
 */
export const Route = createFileRoute('/_authed/$team/settings')({
  component: SettingsView,
})

function SettingsView() {
  const { data: user } = useUser()

  return (
    <div className="p-6">
      <h1 className="mb-6 text-lg font-semibold text-foreground">Settings</h1>

      <section className="max-w-xl space-y-6">
        <div className="rounded-lg border border-border p-4">
          <h2 className="mb-1 text-sm font-medium text-foreground">Profile</h2>
          <p className="mb-3 text-sm text-muted-foreground">
            Your account details.
          </p>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Name</dt>
              <dd className="text-foreground">{user?.display_name ?? '—'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Email</dt>
              <dd className="text-foreground">{user?.email ?? '—'}</dd>
            </div>
          </dl>
        </div>

        <div className="flex items-center justify-between rounded-lg border border-border p-4">
          <div>
            <h2 className="mb-1 text-sm font-medium text-foreground">Appearance</h2>
            <p className="text-sm text-muted-foreground">
              Choose light, dark, or system. Persists across reload and login.
            </p>
          </div>
          <div className="shrink-0">
            <ThemeToggle />
          </div>
        </div>
      </section>
    </div>
  )
}

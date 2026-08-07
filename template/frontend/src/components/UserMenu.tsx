import { LogOut, Settings as SettingsIcon } from 'lucide-react'
import { useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown'
import { useAuth } from '@/contexts/AuthContext'
import { useUser } from '@/hooks/useUser'

/**
 * Topbar user menu — shows the signed-in user (email/avatar), with access to
 * settings and logout. Logout clears the session client-side and routes to
 * /login (handled by AuthContext).
 */
export function UserMenu({ teamKey }: { teamKey?: string }) {
  const { logout } = useAuth()
  const { data: user } = useUser()
  const navigate = useNavigate()

  const settingsTo = teamKey ? ({ to: '/$team/settings', params: { team: teamKey } } as const) : null

  const handleSettings = () => {
    if (settingsTo) {
      void navigate(settingsTo)
    }
  }

  const handleLogout = () => {
    void logout()
  }

  const initials = (user?.display_name || user?.email || '?')
    .slice(0, 2)
    .toUpperCase()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Button variant="ghost" size="icon" className="rounded-full" aria-label="User menu">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
            {initials}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>{user?.email ?? 'Signed in'}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleSettings} disabled={!settingsTo}>
          <SettingsIcon className="h-4 w-4" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="h-4 w-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

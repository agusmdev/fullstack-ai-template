import { useEffect, useState } from 'react'
import { Sun, Moon, Monitor, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
} from '@/components/ui/dropdown'
import {
  applyTheme,
  getStoredTheme,
  watchSystemTheme,
  type ThemeMode,
} from '@/lib/theme'
import { cn } from '@/lib/utils'

const THEME_OPTIONS: { mode: ThemeMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { mode: 'light', label: 'Light', icon: Sun },
  { mode: 'dark', label: 'Dark', icon: Moon },
  { mode: 'system', label: 'System', icon: Monitor },
]

/**
 * Theme toggle — a dropdown offering Light / Dark / System.
 *
 * The chosen mode is applied immediately (no flash), persisted to localStorage,
 * and survives reload and logout/login. "System" tracks `prefers-color-scheme`
 * live via a media-query listener. The trigger icon swaps between sun/moon via
 * the `.dark` class on <html> (pure CSS, no JS-derived icon).
 */
export function ThemeToggle() {
  const [mode, setMode] = useState<ThemeMode>(() => getStoredTheme())

  // Re-sync the active indicator if the OS scheme changes while in system mode.
  useEffect(() => {
    return watchSystemTheme(() => setMode(getStoredTheme()))
  }, [])

  const handleSelect = (next: ThemeMode) => {
    setMode(next)
    applyTheme(next)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Button variant="ghost" size="icon" aria-label="Toggle theme" className="relative">
          <Sun className="h-[1.15rem] w-[1.15rem] scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
          <Moon className="absolute h-[1.15rem] w-[1.15rem] scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Theme</DropdownMenuLabel>
        {THEME_OPTIONS.map(({ mode: m, label, icon: Icon }) => (
          <DropdownMenuItem
            key={m}
            onClick={() => handleSelect(m)}
            aria-checked={mode === m}
            role="menuitemradio"
          >
            <Icon className="h-4 w-4" />
            <span className="flex-1">{label}</span>
            <Check className={cn('h-4 w-4', mode === m ? 'opacity-100' : 'opacity-0')} />
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

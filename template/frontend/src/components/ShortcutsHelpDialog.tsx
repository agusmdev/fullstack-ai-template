import { useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Kbd } from '@/components/Kbd'
import { useKeyboardShortcuts } from '@/contexts/KeyboardShortcutsContext'
import { SHORTCUT_GROUPS } from '@/lib/keyboard'

/**
 * Shortcuts help reference — a discoverable, always-reachable dialog listing
 * every M4 keyboard shortcut (VAL-SHORTCUTS-007).
 *
 * Reachable three ways: the `?` global shortcut, the Topbar help button, and a
 * "Keyboard shortcuts" command in the palette. While open it registers as a
 * modal overlay so single-key shortcuts are blocked (the reference owns the
 * keyboard). Esc / the close button close it via the underlying Radix Dialog
 * (VAL-SHORTCUTS-004).
 */
export function ShortcutsHelpDialog() {
  const { shortcutsHelpOpen, setShortcutsHelpOpen, registerOverlay } = useKeyboardShortcuts()

  // Block single-key shortcuts (c, g, [, ]) while the reference is open.
  useEffect(() => {
    if (!shortcutsHelpOpen) return
    return registerOverlay()
  }, [shortcutsHelpOpen, registerOverlay])

  return (
    <Dialog open={shortcutsHelpOpen} onOpenChange={setShortcutsHelpOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard shortcuts</DialogTitle>
          <DialogDescription>
            The shortcuts below work anywhere in the workspace (except while typing in a text field).
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-5">
          {SHORTCUT_GROUPS.map((group) => (
            <section key={group.heading}>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {group.heading}
              </h3>
              <ul className="flex flex-col gap-1.5" data-testid={`shortcuts-${group.heading.toLowerCase()}`}>
                {group.items.map((item) => (
                  <li key={item.keys} className="flex items-center justify-between gap-4">
                    <span className="text-sm text-foreground">{item.description}</span>
                    <Kbd>{item.keys}</Kbd>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}

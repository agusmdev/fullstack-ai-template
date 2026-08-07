import { useCallback, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  Inbox,
  LayoutGrid,
  Folder,
  Repeat2,
  Eye,
  Plus,
  Keyboard,
} from 'lucide-react'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command'
import { CreateIssueDialog } from '@/components/CreateIssueDialog'
import { ProjectFormDialog } from '@/components/ProjectFormDialog'
import { CycleFormDialog } from '@/components/CycleFormDialog'
import { useCommandPalette } from '@/contexts/CommandPaletteContext'
import { useKeyboardShortcuts } from '@/contexts/KeyboardShortcutsContext'
import { useTeams } from '@/hooks/useTeams'
import { useUser } from '@/hooks/useUser'
import { useTeamRole } from '@/hooks/useTeamRole'
import { useWorkflowStates } from '@/hooks/useWorkflowStates'
import { useLabels } from '@/hooks/useLabels'

/** Typed route targets available in the palette (mirror Sidebar nav). */
type NavTarget =
  | '/$team/issues'
  | '/$team/board'
  | '/$team/projects'
  | '/$team/cycles'
  | '/$team/views'

interface NavEntry {
  label: string
  icon: React.ComponentType<{ className?: string }>
  to: NavTarget
  /** Keywords used to improve fuzzy-match relevance. */
  keywords: string[]
  /** Optional shortcut hint surfaced in the palette (VAL-SHORTCUTS-006). */
  shortcut?: string
}

const NAV_ENTRIES: NavEntry[] = [
  { label: 'Issues', icon: Inbox, to: '/$team/issues', keywords: ['inbox', 'all', 'list'], shortcut: 'G I' },
  { label: 'Board', icon: LayoutGrid, to: '/$team/board', keywords: ['kanban', 'columns'] },
  { label: 'Projects', icon: Folder, to: '/$team/projects', keywords: ['initiatives'] },
  { label: 'Cycles', icon: Repeat2, to: '/$team/cycles', keywords: ['sprint', 'iterations'] },
  { label: 'Views', icon: Eye, to: '/$team/views', keywords: ['saved', 'filters'] },
]

/**
 * Command palette (Cmd+K) — the global quick-navigation + quick-action surface.
 *
 * Open state + create-action state live in `CommandPaletteProvider`; this
 * component renders the modal `CommandDialog` and hosts the create-issue /
 * create-project / create-cycle dialogs so a quick action works from any route
 * (VAL-CMDK-005). Navigation targets close the palette and route without a full
 * reload (VAL-CMDK-004). Esc closes the modal without side effects via the
 * underlying Radix Dialog (VAL-CMDK-006).
 *
 * `cmdk` provides fuzzy search (VAL-CMDK-003), shows the full default command
 * set on an empty query (VAL-CMDK-007), and renders the `CommandEmpty`
 * no-results state when nothing matches (VAL-CMDK-008).
 *
 * Create actions are gated by `canWrite` so guests (read-only) cannot trigger
 * writes from the palette (VAL-CROSS-025).
 */
export function CommandPalette({ teamKey }: { teamKey?: string }) {
  const {
    paletteOpen,
    closePalette,
    createIssueOpen,
    setCreateIssueOpen,
    openCreateIssue,
    createProjectOpen,
    setCreateProjectOpen,
    openCreateProject,
    createCycleOpen,
    setCreateCycleOpen,
    openCreateCycle,
  } = useCommandPalette()
  const { registerOverlay, openShortcutsHelp } = useKeyboardShortcuts()
  const navigate = useNavigate()

  // While the palette is open it owns the keyboard — block single-key global
  // shortcuts (c / g i / [ ]) so typing/search isn't shadowed by them.
  useEffect(() => {
    if (!paletteOpen) return
    return registerOverlay()
  }, [paletteOpen, registerOverlay])

  // Resolve team data for the create dialogs. These are the same React Query
  // keys used by the route pages, so the data is shared (no duplicate requests).
  const { data: teamsData } = useTeams()
  const { data: user } = useUser()
  const { canWrite } = useTeamRole(teamKey)

  const teamId = (teamsData?.items ?? []).find((t) => t.key === teamKey)?.id
  const { data: statesData } = useWorkflowStates(teamId)
  const { data: labelsData } = useLabels(teamId)

  const workflowStates = statesData?.items ?? []
  const labels = labelsData?.items ?? []
  const members = user
    ? [{ id: user.id, name: user.display_name || user.email }]
    : []

  // Run a command: close the palette, then perform the action. Closing first
  // avoids the palette stacking over the opened dialog / causing a nav flash.
  const runCommand = useCallback(
    (action: () => void) => {
      closePalette()
      action()
    },
    [closePalette],
  )

  const navTo = useCallback(
    (to: NavTarget) => {
      runCommand(() =>
        navigate({ to, params: { team: teamKey ?? '' } }),
      )
    },
    [navigate, runCommand, teamKey],
  )

  return (
    <>
      <CommandDialog open={paletteOpen} onOpenChange={(o) => !o && closePalette()}>
        <CommandInput placeholder="Type a command or search…" />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>

          <CommandGroup heading="Navigation">
            {NAV_ENTRIES.map(({ label, icon: Icon, to, keywords, shortcut }) => (
              <CommandItem
                key={to}
                value={`${label} ${keywords.join(' ')}`}
                onSelect={() => navTo(to)}
              >
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span>{label}</span>
                {shortcut && <CommandShortcut>{shortcut}</CommandShortcut>}
              </CommandItem>
            ))}
          </CommandGroup>

          <CommandSeparator />

          <CommandGroup heading="Actions">
            <CommandItem
              value="create issue new add"
              onSelect={() => runCommand(openCreateIssue)}
              disabled={!canWrite}
            >
              <Plus className="h-4 w-4 text-muted-foreground" />
              <span>Create issue</span>
              <CommandShortcut>C</CommandShortcut>
            </CommandItem>
            <CommandItem
              value="create project new add initiative"
              onSelect={() => runCommand(openCreateProject)}
              disabled={!canWrite}
            >
              <Folder className="h-4 w-4 text-muted-foreground" />
              <span>Create project</span>
            </CommandItem>
            <CommandItem
              value="create cycle new add sprint iteration"
              onSelect={() => runCommand(openCreateCycle)}
              disabled={!canWrite}
            >
              <Repeat2 className="h-4 w-4 text-muted-foreground" />
              <span>Create cycle</span>
            </CommandItem>
            <CommandItem
              value="keyboard shortcuts help cheatsheet"
              onSelect={() => runCommand(openShortcutsHelp)}
            >
              <Keyboard className="h-4 w-4 text-muted-foreground" />
              <span>Keyboard shortcuts</span>
              <CommandShortcut>?</CommandShortcut>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </CommandDialog>

      {/* Hosted create dialogs — openable from any route via the palette. */}
      <CreateIssueDialog
        open={createIssueOpen}
        onOpenChange={setCreateIssueOpen}
        teamId={teamId ?? ''}
        workflowStates={workflowStates}
        labels={labels}
        members={members}
      />
      <ProjectFormDialog
        open={createProjectOpen}
        onOpenChange={setCreateProjectOpen}
        teamId={teamId ?? ''}
        members={members}
      />
      <CycleFormDialog
        open={createCycleOpen}
        onOpenChange={setCreateCycleOpen}
        teamId={teamId ?? ''}
      />
    </>
  )
}

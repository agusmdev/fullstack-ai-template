import React from 'react'
import { Check, ChevronDown, Plus, Search, X } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { StatusDot } from '@/components/StatusDot'
import { PriorityIcon, priorityLabel } from '@/components/PriorityIcon'
import { cn } from '@/lib/utils'
import {
  ASSIGNEE_UNASSIGNED,
  PRIORITIES,
  SORT_PRESETS,
  sortKeyToLabel,
  type IssuesQueryParams,
} from '@/types/issue'
import type { WorkflowState } from '@/types/workflow-state'
import type { Label } from '@/types/label'

/** A selectable option for a single-select filter dropdown. */
interface FilterOption<T extends string> {
  value: T
  label: string
  /** Optional leading icon node (dot/avatar/glyph). */
  leading?: React.ReactNode
}

interface SingleFilterDropdownProps<T extends string> {
  /** Filter name shown when nothing is selected (e.g. "Status"). */
  name: string
  value: T | null
  onChange: (value: T | null) => void
  options: FilterOption<T>[]
  /** Label for the "clear" option that resets the filter (e.g. "All statuses"). */
  allLabel?: string
  disabled?: boolean
}

/**
 * A single-select filter dropdown. Shows a "+ Name" trigger when inactive and
 * the selected option when active; selecting an option applies it, and the
 * "All …" item clears the filter. Auto-closes on select.
 */
function SingleFilterDropdown<T extends string>({
  name,
  value,
  onChange,
  options,
  allLabel,
  disabled,
}: SingleFilterDropdownProps<T>) {
  const selected = options.find((o) => o.value === value) ?? null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled}
          className={cn(
            'gap-1.5 font-normal',
            selected && 'border-primary/50 text-foreground',
          )}
        >
          {selected ? (
            <>
              {selected.leading}
              <span className="max-w-[8rem] truncate">{selected.label}</span>
            </>
          ) : (
            <>
              <Plus className="h-3 w-3 text-muted-foreground" />
              <span>{name}</span>
            </>
          )}
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="min-w-[14rem]">
        <DropdownMenuLabel>{name}</DropdownMenuLabel>
        <DropdownMenuItem
          onClick={() => onChange(null)}
          className={cn('gap-2', value === null && 'font-medium')}
        >
          <span className="flex-1">{allLabel ?? `All ${name.toLowerCase()}`}</span>
          {value === null && <Check className="h-3.5 w-3.5" />}
        </DropdownMenuItem>
        {options.length > 0 && <DropdownMenuSeparator />}
        {options.map((option) => (
          <DropdownMenuItem
            key={option.value}
            onClick={() => onChange(option.value)}
            className="gap-2"
          >
            {option.leading}
            <span className="flex-1 truncate">{option.label}</span>
            {option.value === value && <Check className="h-3.5 w-3.5" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

/** Renders initials in a small avatar. */
function Avatar({ name }: { name: string }) {
  const initials = name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
  return (
    <span
      className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-primary/15 text-[9px] font-semibold text-primary"
      aria-hidden
    >
      {initials || '?'}
    </span>
  )
}

export interface IssueFiltersBarProps {
  /** Current filter/search/sort state. */
  params: IssuesQueryParams
  /** Raw (un-debounced) search input value. */
  searchInput: string
  onSearchInputChange: (value: string) => void
  onParamsChange: (patch: Partial<IssuesQueryParams>) => void
  onClear: () => void
  /** Whether any filter/search/sort is active (controls the Clear button). */
  hasActive: boolean
  /** Options. */
  workflowStates: WorkflowState[]
  labels: Label[]
  /** Known assignable members (id + display name). */
  members: { id: string; name: string }[]
  disabled?: boolean
}

/**
 * The issues filter bar.
 *
 * Drives server-side filtering/search/sort (VAL-ISSUES-019–028). All four
 * filters (status, priority, assignee incl. Unassigned, label) compose with AND
 * semantics because they are independent query params intersected by the
 * backend (VAL-ISSUES-023). The Clear button restores the full list
 * (VAL-ISSUES-024). Search is a case-insensitive substring handled server-side
 * (VAL-ISSUES-025). The search input is controlled by the caller, which debounces
 * it before feeding the debounced value into the query.
 */
export function IssueFiltersBar({
  params,
  searchInput,
  onSearchInputChange,
  onParamsChange,
  onClear,
  hasActive,
  workflowStates,
  labels,
  members,
  disabled,
}: IssueFiltersBarProps) {
  const statusOptions: FilterOption<string>[] = workflowStates.map((s) => ({
    value: s.id,
    label: s.name,
    leading: <StatusDot color={s.color} type={s.type} />,
  }))

  const priorityOptions: FilterOption<string>[] = PRIORITIES.map((p) => ({
    value: String(p.value),
    label: p.label,
    leading: <PriorityIcon priority={p.value} />,
  }))

  const assigneeOptions: FilterOption<string>[] = [
    {
      value: ASSIGNEE_UNASSIGNED,
      label: 'Unassigned',
    },
    ...members.map((m) => ({
      value: m.id,
      label: m.name,
      leading: <Avatar name={m.name} />,
    })),
  ]

  const labelOptions: FilterOption<string>[] = labels.map((l) => ({
    value: l.id,
    label: l.name,
    leading: <StatusDot color={l.color} />,
  }))

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Search */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          value={searchInput}
          onChange={(e) => onSearchInputChange(e.target.value)}
          placeholder="Filter by title…"
          aria-label="Search issues by title"
          className="h-8 w-56 pl-8 text-sm"
          disabled={disabled}
        />
        {searchInput && (
          <button
            type="button"
            onClick={() => onSearchInputChange('')}
            aria-label="Clear search"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-sm p-0.5 text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Filters */}
      <SingleFilterDropdown
        name="Status"
        value={params.status_id ?? null}
        onChange={(v) => onParamsChange({ status_id: v })}
        options={statusOptions}
        allLabel="All statuses"
        disabled={disabled}
      />
      <SingleFilterDropdown
        name="Priority"
        value={params.priority != null ? String(params.priority) : null}
        onChange={(v) => onParamsChange({ priority: v == null ? null : Number(v) })}
        options={priorityOptions}
        allLabel="All priorities"
        disabled={disabled}
      />
      <SingleFilterDropdown
        name="Assignee"
        value={params.assignee ?? null}
        onChange={(v) => onParamsChange({ assignee: v })}
        options={assigneeOptions}
        allLabel="All assignees"
        disabled={disabled}
      />
      <SingleFilterDropdown
        name="Label"
        value={params.label_id ?? null}
        onChange={(v) => onParamsChange({ label_id: v })}
        options={labelOptions}
        allLabel="All labels"
        disabled={disabled}
      />

      <div className="ml-auto flex items-center gap-2">
        {/* Sort */}
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button type="button" variant="ghost" size="sm" disabled={disabled} className="gap-1.5 font-normal">
              <span className="text-muted-foreground">Sort:</span>
              <span>{sortKeyToLabel(params.sort)}</span>
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-[14rem]">
            <DropdownMenuLabel>Sort by</DropdownMenuLabel>
            {SORT_PRESETS.map((preset) => (
              <DropdownMenuItem
                key={preset.key}
                onClick={() => onParamsChange({ sort: preset.key })}
                className="gap-2"
              >
                <span className="flex-1">{preset.label}</span>
                {params.sort === preset.key && <Check className="h-3.5 w-3.5" />}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {hasActive && (
          <Button type="button" variant="ghost" size="sm" onClick={onClear} disabled={disabled} className="gap-1.5 font-normal text-muted-foreground">
            <X className="h-3.5 w-3.5" />
            Clear
          </Button>
        )}
      </div>
    </div>
  )
}

// Re-export so the create/picker area can reuse the glyph helper if needed.
export { priorityLabel }

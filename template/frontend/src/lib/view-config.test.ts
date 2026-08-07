import { describe, it, expect } from 'vitest'
import { DEFAULT_SORT_KEY } from '@/types/issue'
import type { IssueUrlSearch } from '@/lib/issue-search'
import type { View } from '@/types/view'
import {
  viewToUrlSearch,
  urlSearchToViewConfig,
  viewMatchesSearch,
  hasActiveViewConfig,
  DEFAULT_GROUP_BY,
} from '@/lib/view-config'

function makeView(overrides: Partial<View> = {}): View {
  return {
    id: 'v-1',
    owner_id: 'u-1',
    team_id: 't-1',
    name: 'Urgent bugs',
    filters: { status_id: 'st-1', priority: 0 },
    group_by: 'status',
    order_by: 'priority',
    description: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

describe('urlSearchToViewConfig (save)', () => {
  it('captures filters + group_by + sort from the current URL search', () => {
    const search: IssueUrlSearch = {
      q: 'login',
      status_id: 'st-1',
      priority: 0,
      assignee: 'u-2',
      label_id: 'l-1',
      sort: 'priority',
    }
    const config = urlSearchToViewConfig(search)
    expect(config.filters).toEqual({
      q: 'login',
      status_id: 'st-1',
      priority: 0,
      assignee: 'u-2',
      label_id: 'l-1',
    })
    expect(config.group_by).toBe(DEFAULT_GROUP_BY)
    expect(config.order_by).toBe('priority')
  })

  it('omits empty filter values so the snapshot is minimal', () => {
    const config = urlSearchToViewConfig({ sort: DEFAULT_SORT_KEY })
    expect(config.filters).toEqual({})
    expect(config.order_by).toBe(DEFAULT_SORT_KEY)
  })

  it('defaults order_by when sort is absent', () => {
    const config = urlSearchToViewConfig({})
    expect(config.order_by).toBe(DEFAULT_SORT_KEY)
  })
})

describe('viewToUrlSearch (apply)', () => {
  it('rebuilds the URL search from a saved view', () => {
    const view = makeView()
    const search = viewToUrlSearch(view)
    expect(search).toEqual({
      status_id: 'st-1',
      priority: 0,
      sort: 'priority',
    })
  })

  it('falls back to the default sort when order_by is null', () => {
    const search = viewToUrlSearch(makeView({ order_by: null }))
    expect(search.sort).toBe(DEFAULT_SORT_KEY)
  })

  it('round-trips save → apply', () => {
    const original: IssueUrlSearch = {
      q: 'crash',
      status_id: 'st-9',
      priority: 2,
      assignee: 'unassigned',
      label_id: 'l-3',
      sort: 'updated',
    }
    const config = urlSearchToViewConfig(original)
    const view = makeView({
      filters: config.filters as Record<string, unknown>,
      order_by: config.order_by,
    })
    const restored = viewToUrlSearch(view)
    expect(restored).toEqual(original)
  })
})

describe('viewMatchesSearch (active highlight + dirty detection)', () => {
  it('matches when the current search equals the view config', () => {
    const view = makeView()
    expect(
      viewMatchesSearch(view, { status_id: 'st-1', priority: 0, sort: 'priority' }),
    ).toBe(true)
  })

  it('does not match after a filter is changed (dirty)', () => {
    const view = makeView()
    // User applied the view, then changed the priority filter.
    expect(
      viewMatchesSearch(view, { status_id: 'st-1', priority: 1, sort: 'priority' }),
    ).toBe(false)
  })

  it('does not match after the sort is changed (dirty)', () => {
    const view = makeView()
    expect(
      viewMatchesSearch(view, { status_id: 'st-1', priority: 0, sort: 'newest' }),
    ).toBe(false)
  })

  it('treats missing sort and default sort as equivalent', () => {
    const view = makeView({
      filters: {} as Record<string, unknown>,
      order_by: DEFAULT_SORT_KEY,
    })
    expect(viewMatchesSearch(view, {})).toBe(true)
    expect(viewMatchesSearch(view, { sort: DEFAULT_SORT_KEY })).toBe(true)
  })

  it('matches a default (no-filter) view against a cleared search', () => {
    const view = makeView({
      filters: {} as Record<string, unknown>,
      order_by: DEFAULT_SORT_KEY,
    })
    expect(viewMatchesSearch(view, { sort: DEFAULT_SORT_KEY })).toBe(true)
  })
})

describe('hasActiveViewConfig', () => {
  it('is false for the default cleared state', () => {
    expect(hasActiveViewConfig({ sort: DEFAULT_SORT_KEY })).toBe(false)
    expect(hasActiveViewConfig({})).toBe(false)
  })

  it('is true when any filter is set', () => {
    expect(hasActiveViewConfig({ status_id: 'st-1', sort: DEFAULT_SORT_KEY })).toBe(true)
    expect(hasActiveViewConfig({ q: 'bug', sort: DEFAULT_SORT_KEY })).toBe(true)
    expect(hasActiveViewConfig({ priority: 0, sort: DEFAULT_SORT_KEY })).toBe(true)
  })

  it('is true when sort deviates from the default', () => {
    expect(hasActiveViewConfig({ sort: 'priority' })).toBe(true)
  })
})

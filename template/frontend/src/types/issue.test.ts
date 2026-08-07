import { describe, it, expect } from 'vitest'
import {
  ASSIGNEE_UNASSIGNED,
  DEFAULT_SORT_KEY,
  SORT_PRESETS,
  hasActiveIssueFilters,
  serializeIssueParams,
  sortKeyToOrderBy,
  sortKeyToLabel,
  type IssuesQueryParams,
} from './issue'

const empty: IssuesQueryParams = { sort: DEFAULT_SORT_KEY }

describe('hasActiveIssueFilters', () => {
  it('is false for the default (no-filter) view', () => {
    expect(hasActiveIssueFilters(empty)).toBe(false)
    expect(hasActiveIssueFilters({})).toBe(false)
  })

  it('is true when any single filter is set', () => {
    expect(hasActiveIssueFilters({ status_id: 's-1' })).toBe(true)
    expect(hasActiveIssueFilters({ priority: 0 })).toBe(true)
    expect(hasActiveIssueFilters({ assignee: 'u-1' })).toBe(true)
    expect(hasActiveIssueFilters({ assignee: ASSIGNEE_UNASSIGNED })).toBe(true)
    expect(hasActiveIssueFilters({ label_id: 'l-1' })).toBe(true)
    expect(hasActiveIssueFilters({ search: 'bug' })).toBe(true)
  })

  it('is true for a non-default sort', () => {
    expect(hasActiveIssueFilters({ sort: 'priority' })).toBe(true)
    expect(hasActiveIssueFilters({ sort: 'oldest' })).toBe(true)
  })

  it('treats a whitespace-only search as inactive', () => {
    expect(hasActiveIssueFilters({ search: '   ' })).toBe(false)
  })
})

describe('serializeIssueParams', () => {
  it('serializes to "" for the default view (stable key)', () => {
    expect(serializeIssueParams(empty)).toBe('')
    expect(serializeIssueParams({})).toBe('')
  })

  it('encodes every active dimension distinctly', () => {
    expect(serializeIssueParams({ search: 'Bug Report' })).toBe('q:Bug Report')
    expect(serializeIssueParams({ status_id: 's-1' })).toBe('s:s-1')
    expect(serializeIssueParams({ priority: 2 })).toBe('p:2')
    expect(serializeIssueParams({ assignee: 'u-1' })).toBe('a:u-1')
    expect(serializeIssueParams({ assignee: ASSIGNEE_UNASSIGNED })).toBe(
      `a:${ASSIGNEE_UNASSIGNED}`,
    )
    expect(serializeIssueParams({ label_id: 'l-1' })).toBe('l:l-1')
    expect(serializeIssueParams({ sort: 'priority' })).toBe('o:priority')
  })

  it('is stable regardless of how combined filters are provided', () => {
    const a = serializeIssueParams({
      status_id: 's-1',
      priority: 0,
      assignee: 'u-1',
      label_id: 'l-1',
    })
    expect(a).toBe('s:s-1|p:0|a:u-1|l:l-1')
  })

  it('ignores whitespace-only search', () => {
    expect(serializeIssueParams({ search: '   ' })).toBe('')
  })
})

describe('sort presets', () => {
  it('default sort is newest-first (created desc)', () => {
    expect(DEFAULT_SORT_KEY).toBe('newest')
    expect(sortKeyToOrderBy('newest')).toEqual(['-created_at'])
    expect(sortKeyToOrderBy(undefined)).toEqual(['-created_at'])
    expect(sortKeyToLabel('newest')).toBe('Newest first')
  })

  it('oldest flips created to ascending (VAL-ISSUES-026 toggle)', () => {
    expect(sortKeyToOrderBy('oldest')).toEqual(['created_at'])
  })

  it('updated sorts by updated_at desc (VAL-ISSUES-027)', () => {
    expect(sortKeyToOrderBy('updated')).toEqual(['-updated_at'])
  })

  it('priority sorts ascending with a deterministic created tiebreaker (VAL-ISSUES-028)', () => {
    expect(sortKeyToOrderBy('priority')).toEqual(['priority', '-created_at'])
  })

  it('every preset has a unique key and non-empty order_by', () => {
    const keys = SORT_PRESETS.map((p) => p.key)
    expect(new Set(keys).size).toBe(keys.length)
    for (const preset of SORT_PRESETS) {
      expect(preset.order_by.length).toBeGreaterThan(0)
    }
  })
})

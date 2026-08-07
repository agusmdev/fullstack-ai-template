import { describe, it, expect } from 'vitest'
import {
  validateIssueSearch,
  urlSearchToParams,
  defaultIssueSearch,
  type IssueUrlSearch,
} from './issue-search'
import { DEFAULT_SORT_KEY } from '@/types/issue'

describe('validateIssueSearch', () => {
  it('defaults sort to newest when absent', () => {
    expect(validateIssueSearch({})).toEqual({ sort: DEFAULT_SORT_KEY })
  })

  it('parses all filter fields from raw input', () => {
    const raw = {
      q: '  bug  ',
      status_id: 'st-1',
      priority: '2',
      assignee: 'unassigned',
      label_id: 'lb-1',
      sort: 'priority',
    }
    expect(validateIssueSearch(raw)).toEqual({
      q: 'bug',
      status_id: 'st-1',
      priority: 2,
      assignee: 'unassigned',
      label_id: 'lb-1',
      sort: 'priority',
    })
  })

  it('drops empty / junk values', () => {
    expect(validateIssueSearch({ q: '   ', status_id: '', priority: 'abc' })).toEqual({
      sort: DEFAULT_SORT_KEY,
    })
  })

  it('treats empty-string priority as absent', () => {
    expect(validateIssueSearch({ priority: '' })).toEqual({ sort: DEFAULT_SORT_KEY })
  })

  it('preserves priority 0 (urgent)', () => {
    expect(validateIssueSearch({ priority: 0 })).toEqual({
      sort: DEFAULT_SORT_KEY,
      priority: 0,
    })
  })
})

describe('urlSearchToParams', () => {
  it('maps all fields to IssuesQueryParams with null defaults', () => {
    const search: IssueUrlSearch = {
      q: 'bug',
      status_id: 'st-1',
      priority: 1,
      assignee: 'u-1',
      label_id: 'lb-1',
      sort: 'updated',
    }
    expect(urlSearchToParams(search)).toEqual({
      search: 'bug',
      status_id: 'st-1',
      priority: 1,
      assignee: 'u-1',
      label_id: 'lb-1',
      sort: 'updated',
    })
  })

  it('maps an empty search to default params', () => {
    expect(urlSearchToParams({ sort: DEFAULT_SORT_KEY })).toEqual({
      search: undefined,
      status_id: null,
      priority: null,
      assignee: null,
      label_id: null,
      sort: DEFAULT_SORT_KEY,
    })
  })
})

describe('defaultIssueSearch', () => {
  it('returns only the default sort', () => {
    expect(defaultIssueSearch()).toEqual({ sort: DEFAULT_SORT_KEY })
  })
})

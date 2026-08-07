import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useDebounce } from '@/hooks/useDebounce'
import {
  defaultIssueSearch,
  urlSearchToParams,
  type IssueUrlSearch,
} from '@/lib/issue-search'
import {
  DEFAULT_SORT_KEY,
  hasActiveIssueFilters,
  type IssuesQueryParams,
} from '@/types/issue'

/** Debounce delay (ms) for the title search input before committing to the URL. */
const SEARCH_DEBOUNCE_MS = 250

/** Return type of {@link useIssueFilters}. */
export interface IssueFiltersState {
  /** Query params derived from the URL search (fed to `useIssues`). */
  params: IssuesQueryParams
  /** Raw (un-debounced) search input value (for the text field). */
  searchInput: string
  setSearchInput: (value: string) => void
  /** Apply a partial filter patch (writes to URL, replacing history). */
  setParams: (patch: Partial<IssuesQueryParams>) => void
  /** Reset all filters to defaults (writes to URL). */
  clear: () => void
  /** Whether any filter/search/sort deviates from the default. */
  hasActive: boolean
  /** The raw URL search object (for the list↔board toggle Link). */
  urlSearch: IssueUrlSearch
}

/**
 * Shared filter/search/sort state for the Issues list and Board views.
 *
 * Filters live in the **URL search params** (validated by both routes via
 * `validateIssueSearch`) so the list↔board toggle preserves the exact same
 * scope + filters — switching views is just a route change carrying the same
 * query string (VAL-BOARD-005).
 *
 * The title-search text input is local state, debounced, then committed to the
 * URL so typing doesn't fire a request per keystroke. Filter dropdown changes
 * write to the URL immediately (with `replace` to avoid history pollution).
 *
 * @param urlSearch — the validated URL search from the route's `useSearch()`.
 */
export function useIssueFilters(urlSearch: IssueUrlSearch): IssueFiltersState {
  const navigate = useNavigate()

  const params = urlSearchToParams(urlSearch)

  // Search input: local state synced from URL, debounced before committing.
  const [searchInput, setSearchInput] = useState(urlSearch.q ?? '')
  const debouncedSearch = useDebounce(searchInput, SEARCH_DEBOUNCE_MS)

  // Commit the debounced search text to the URL (replace, not push).
  useEffect(() => {
    const committed = urlSearch.q ?? ''
    if (debouncedSearch !== committed) {
      void navigate({
        to: '.',
        search: (prev: IssueUrlSearch) => ({
          ...prev,
          q: debouncedSearch.trim() || undefined,
        }),
        replace: true,
      })
    }
  }, [debouncedSearch]) // intentional: only re-fire on debounce settle

  // Sync the local input when the URL `q` changes externally (Clear, toggle).
  useEffect(() => {
    setSearchInput(urlSearch.q ?? '')
  }, [urlSearch.q])

  /** Convert an IssuesQueryParams patch to a URL search patch and navigate. */
  const setParams = useCallback(
    (patch: Partial<IssuesQueryParams>) => {
      const urlPatch: Partial<IssueUrlSearch> = {}
      if (patch.status_id !== undefined)
        urlPatch.status_id = patch.status_id || undefined
      if (patch.priority !== undefined)
        urlPatch.priority = patch.priority ?? undefined
      if (patch.assignee !== undefined)
        urlPatch.assignee = patch.assignee || undefined
      if (patch.label_id !== undefined)
        urlPatch.label_id = patch.label_id || undefined
      if (patch.sort !== undefined) urlPatch.sort = patch.sort
      void navigate({
        to: '.',
        search: (prev: IssueUrlSearch) => ({ ...prev, ...urlPatch }),
        replace: true,
      })
    },
    [navigate],
  )

  const clear = useCallback(() => {
    setSearchInput('')
    void navigate({
      to: '.',
      search: () => defaultIssueSearch(),
      replace: true,
    })
  }, [navigate])

  return {
    params,
    searchInput,
    setSearchInput,
    setParams,
    clear,
    hasActive: hasActiveIssueFilters(params),
    urlSearch,
  }
}

/** Re-export for convenience (used by route definitions). */
export { DEFAULT_SORT_KEY }

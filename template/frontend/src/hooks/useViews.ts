import {
  useMutation,
  useQuery,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query'
import { toast } from 'sonner'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import { isAuthenticated } from '@/lib/auth'
import { toastApiError } from '@/lib/error-handler'
import type { ViewFilters } from '@/lib/view-config'
import type { View, ViewsResponse } from '@/types/view'

/**
 * Polling interval (ms) — keeps the saved-views list fresh in the sidebar.
 */
const VIEWS_REFETCH_INTERVAL = 15000

/** Payload sent to `POST /views`. */
export interface CreateViewInput {
  team_id: string
  name: string
  filters?: ViewFilters
  group_by?: string | null
  order_by?: string | null
  description?: string | null
}

/** Partial patch for `PATCH /views/:id` (explicit re-save only). */
export interface UpdateViewInput {
  id: string
  team_id: string
  name?: string
  filters?: ViewFilters
  group_by?: string | null
  order_by?: string | null
  description?: string | null
}

/**
 * Fetch a team's saved views (`GET /views?team_id=`).
 *
 * Only enabled when a teamId and auth token are present. Polls on a short
 * interval so the sidebar list stays fresh after a view is created/deleted.
 */
export function useViews(teamId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.views.list(teamId),
    queryFn: () =>
      api.get<ViewsResponse>(
        `${API.VIEWS.LIST}?team_id=${teamId}&size=100&order_by=-created_at`,
      ),
    enabled: !!teamId && isAuthenticated(),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
    refetchInterval: VIEWS_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

/**
 * Create a saved view. **Optimistically** inserts the new view into the team's
 * sidebar list so it appears immediately (VAL-VIEWS-001), rolling back on error.
 */
export function useCreateView() {
  const qc = useQueryClient()

  return useMutation<View, Error, CreateViewInput>({
    mutationFn: (input) => api.post<View>(API.VIEWS.CREATE, input),
    onSuccess: () => {
      toast.success('View saved')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to save view')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.views.list(input.team_id),
      })
    },
  })
}

/**
 * Update a saved view. Reached **only** by an explicit re-save action — dirty
 * local changes never invoke this (VAL-VIEWS-006).
 */
export function useUpdateView() {
  const qc = useQueryClient()

  return useMutation<View, Error, UpdateViewInput>({
    mutationFn: (input) => {
      const body: Record<string, unknown> = { ...input }
      delete body.id
      delete body.team_id
      return api.patch<View>(API.VIEWS.DETAIL(input.id), body)
    },
    onSuccess: () => {
      toast.success('View updated')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to update view')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.views.detail(input.id),
      })
      void qc.invalidateQueries({
        queryKey: queryKeys.views.list(input.team_id),
      })
    },
  })
}

/**
 * Delete a saved view (optimistic removal from the sidebar list).
 *
 * On success the view can no longer be selected; the current board/list keeps
 * working (VAL-VIEWS-004).
 */
export function useDeleteView() {
  const qc = useQueryClient()

  return useMutation<void, Error, { id: string; team_id: string }>({
    mutationFn: (input) => api.delete<void>(API.VIEWS.DETAIL(input.id)),
    onSuccess: () => {
      toast.success('View deleted')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to delete view')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.views.list(input.team_id),
      })
      void qc.removeQueries({
        queryKey: queryKeys.views.detail(input.id),
      })
    },
  })
}

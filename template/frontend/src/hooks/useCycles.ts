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
import type {
  Cycle,
  CyclesResponse,
} from '@/types/cycle'

/**
 * Polling interval (ms) — keeps the active cycle list fresh.
 */
const CYCLES_REFETCH_INTERVAL = 10000

/** Payload sent to `POST /cycles`. */
export interface CreateCycleInput {
  team_id: string
  name: string
  starts_at: string
  ends_at: string
  completed_at?: string | null
}

/** Partial patch for `PATCH /cycles/:id`. */
export interface UpdateCycleInput {
  id: string
  team_id: string
  name?: string
  starts_at?: string
  ends_at?: string
  completed_at?: string | null
}

/**
 * Fetch a team's cycles (`GET /cycles?team_id=`).
 *
 * Only enabled when a teamId and auth token are present. Polls on a short
 * interval so cycle lists stay fresh after an issue is assigned/unassigned.
 */
export function useCycles(teamId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.cycles.list(teamId),
    queryFn: () =>
      api.get<CyclesResponse>(
        `${API.CYCLES.LIST}?team_id=${teamId}&size=100&order_by=-created_at`,
      ),
    enabled: !!teamId && isAuthenticated(),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
    refetchInterval: CYCLES_REFETCH_INTERVAL,
    refetchOnWindowFocus: true,
  })
}

/**
 * Fetch a single cycle by ID (`GET /cycles/:id`).
 */
export function useCycle(cycleId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.cycles.detail(cycleId!),
    queryFn: () => api.get<Cycle>(API.CYCLES.DETAIL(cycleId!)),
    enabled: !!cycleId && isAuthenticated(),
  })
}

/**
 * Resolve cycle IDs to names for badge display. Returns a function
 * ``cycleId → Cycle | undefined`` from the cached list.
 */
export function useCycleLookup(teamId: string | undefined) {
  const { data } = useCycles(teamId)
  const map = new Map((data?.items ?? []).map((c) => [c.id, c]))
  return (cycleId: string | null | undefined): Cycle | undefined =>
    cycleId ? map.get(cycleId) : undefined
}

/**
 * Create a cycle. Invalidates the team's cycle list so the new cycle appears
 * (VAL-CYCLES-001).
 */
export function useCreateCycle() {
  const qc = useQueryClient()

  return useMutation<Cycle, Error, CreateCycleInput>({
    mutationFn: (input) => api.post<Cycle>(API.CYCLES.CREATE, input),
    onSuccess: () => {
      toast.success('Cycle created')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to create cycle')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.cycles.list(input.team_id),
      })
    },
  })
}

/**
 * Update a cycle. Invalidates detail + list caches.
 */
export function useUpdateCycle() {
  const qc = useQueryClient()

  return useMutation<Cycle, Error, UpdateCycleInput>({
    mutationFn: (input) => {
      const body: Record<string, unknown> = { ...input }
      delete body.id
      delete body.team_id
      return api.patch<Cycle>(API.CYCLES.DETAIL(input.id), body)
    },
    onSuccess: () => {
      toast.success('Cycle updated')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to update cycle')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.cycles.detail(input.id),
      })
      void qc.invalidateQueries({
        queryKey: queryKeys.cycles.list(input.team_id),
      })
    },
  })
}

/**
 * Delete a cycle (optimistic removal). Issues are detached server-side
 * (SET NULL); the issues list is invalidated to reflect the cleared badges.
 */
export function useDeleteCycle() {
  const qc = useQueryClient()

  return useMutation<void, Error, { id: string; team_id: string }>({
    mutationFn: (input) => api.delete<void>(API.CYCLES.DETAIL(input.id)),
    onSuccess: () => {
      toast.success('Cycle deleted')
    },
    onError: (error) => {
      toastApiError(error, 'Failed to delete cycle')
    },
    onSettled: (_data, _error, input) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.cycles.list(input.team_id),
      })
      void qc.removeQueries({
        queryKey: queryKeys.cycles.detail(input.id),
      })
      // Issues may have had their cycle_id cleared (SET NULL on delete).
      void qc.invalidateQueries({ queryKey: queryKeys.issues.list(input.team_id) })
    },
  })
}

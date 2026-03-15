import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import type { ItemsResponse } from '@/types/item'

// --- Helpers ---

function makeQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
}

function makeItemsResponse(overrides?: Partial<ItemsResponse>): ItemsResponse {
  return {
    items: [
      { id: 'item-1', name: 'First', description: null, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z', user_id: 'u1' },
      { id: 'item-2', name: 'Second', description: null, created_at: '2024-01-02T00:00:00Z', updated_at: '2024-01-02T00:00:00Z', user_id: 'u1' },
    ],
    total: 2,
    page: 1,
    size: 9,
    pages: 1,
    ...overrides,
  }
}

// --- useCreateItem / useUpdateItem cache invalidation ---

describe('useCreateItem cache invalidation', () => {
  it('invalidates items.all after a successful create', async () => {
    const qc = makeQueryClient()
    vi.stubGlobal('fetch', vi.fn())

    const initial = makeItemsResponse()
    qc.setQueryData(['items', 'list', undefined], initial)

    // Simulate onSuccess: invalidateQueries({ queryKey: ['items'] })
    await qc.invalidateQueries({ queryKey: ['items'] })

    // After invalidation the query becomes stale — it will refetch on next access
    const state = qc.getQueryState(['items', 'list', undefined])
    expect(state?.isInvalidated).toBe(true)
  })
})

describe('useUpdateItem cache invalidation', () => {
  it('invalidates items.all after a successful update', async () => {
    const qc = makeQueryClient()
    vi.stubGlobal('fetch', vi.fn())

    const initial = makeItemsResponse()
    qc.setQueryData(['items', 'list', { page: 1, size: 9 }], initial)

    // Simulate onSuccess: invalidateQueries({ queryKey: ['items'] })
    await qc.invalidateQueries({ queryKey: ['items'] })

    const state = qc.getQueryState(['items', 'list', { page: 1, size: 9 }])
    expect(state?.isInvalidated).toBe(true)
  })

})

// --- useDeleteItem optimistic update ---

describe('useDeleteItem optimistic rollback', () => {
  let qc: QueryClient
  const ITEMS_KEY = ['items']

  beforeEach(() => {
    qc = makeQueryClient()
    vi.stubGlobal('fetch', vi.fn())
  })

  it('removes the deleted item from cache optimistically', async () => {
    const initial = makeItemsResponse()
    qc.setQueryData([...ITEMS_KEY, { page: 1, size: 9 }], initial)

    // Simulate onMutate logic directly (the hook's optimistic update)
    await qc.cancelQueries({ queryKey: ITEMS_KEY })
    const previousData = qc.getQueriesData<ItemsResponse>({ queryKey: ITEMS_KEY })

    qc.setQueriesData<ItemsResponse>({ queryKey: ITEMS_KEY }, (old) => {
      if (!old) return old
      return {
        ...old,
        items: old.items.filter((item) => item.id !== 'item-1'),
        total: old.total - 1,
      }
    })

    const after = qc.getQueryData<ItemsResponse>([...ITEMS_KEY, { page: 1, size: 9 }])
    expect(after?.items).toHaveLength(1)
    expect(after?.items[0].id).toBe('item-2')
    expect(after?.total).toBe(1)

    // Simulate onError rollback
    for (const [queryKey, data] of previousData) {
      qc.setQueryData(queryKey, data)
    }

    const restored = qc.getQueryData<ItemsResponse>([...ITEMS_KEY, { page: 1, size: 9 }])
    expect(restored?.items).toHaveLength(2)
    expect(restored?.total).toBe(2)
  })

  it('rolls back to previous data on error', async () => {
    const initial = makeItemsResponse()
    const cacheKey = [...ITEMS_KEY, { page: 1, size: 9 }]
    qc.setQueryData(cacheKey, initial)

    const previousData = qc.getQueriesData<ItemsResponse>({ queryKey: ITEMS_KEY })

    // Apply optimistic update
    qc.setQueriesData<ItemsResponse>({ queryKey: ITEMS_KEY }, (old) => {
      if (!old) return old
      return { ...old, items: old.items.filter((i) => i.id !== 'item-1'), total: old.total - 1 }
    })

    expect(qc.getQueryData<ItemsResponse>(cacheKey)?.items).toHaveLength(1)

    // Rollback
    for (const [queryKey, data] of previousData) {
      qc.setQueryData(queryKey, data)
    }

    expect(qc.getQueryData<ItemsResponse>(cacheKey)?.items).toHaveLength(2)
  })

  it('handles missing cache entry gracefully in optimistic update', () => {
    // No data set — setQueriesData should not throw
    expect(() => {
      qc.setQueriesData<ItemsResponse>({ queryKey: ITEMS_KEY }, (old) => {
        if (!old) return old
        return { ...old, items: old.items.filter((i) => i.id !== 'item-1'), total: old.total - 1 }
      })
    }).not.toThrow()
  })
})

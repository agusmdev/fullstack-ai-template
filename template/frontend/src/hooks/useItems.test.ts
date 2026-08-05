import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { useItems, useCreateItem, useUpdateItem, useDeleteItem } from './useItems'
import { queryKeys } from '@/lib/query-keys'
import type { Item, ItemsResponse } from '@/types/item'

// --- Helpers ---

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}

function makeItem(overrides?: Partial<Item>): Item {
  return {
    id: 'item-1',
    name: 'First',
    description: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    deleted_at: null,
    user_id: 'u1',
    ...overrides,
  }
}

function makeItemsResponse(items: Item[], overrides?: Partial<ItemsResponse>): ItemsResponse {
  return { items, total: items.length, page: 1, size: 9, pages: 1, ...overrides }
}

function makeWrapper(qc: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: qc }, children)
  }
}

const apiMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}))

vi.mock('@/lib/api-client', () => ({ api: apiMock }))

// --- Tests ---

beforeEach(() => {
  apiMock.get.mockReset()
  apiMock.post.mockReset()
  apiMock.patch.mockReset()
  apiMock.delete.mockReset()
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('useItems', () => {
  it('fetches items from the list endpoint with the built URL', async () => {
    const qc = makeQueryClient()
    const items = makeItemsResponse([makeItem()])
    apiMock.get.mockResolvedValue(items)

    const { result } = renderHook(() => useItems(), { wrapper: makeWrapper(qc) })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/items')
    expect(result.current.data).toEqual(items)
  })

  it('passes params through to the URL builder', async () => {
    const qc = makeQueryClient()
    apiMock.get.mockResolvedValue(makeItemsResponse([]))

    const { result } = renderHook(() => useItems({ page: 2, size: 9, name: 'foo' }), {
      wrapper: makeWrapper(qc),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiMock.get).toHaveBeenCalledWith('/items?page=2&size=9&name__ilike=foo')
  })

  it('exposes the error state when the request fails', async () => {
    const qc = makeQueryClient()
    apiMock.get.mockRejectedValue(new Error('boom'))

    const { result } = renderHook(() => useItems(), { wrapper: makeWrapper(qc) })

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.data).toBeUndefined()
  })

  it('does not fetch when enabled is false', async () => {
    const qc = makeQueryClient()
    apiMock.get.mockResolvedValue(makeItemsResponse([]))

    const { result } = renderHook(() => useItems(undefined, false), {
      wrapper: makeWrapper(qc),
    })

    expect(result.current.fetchStatus).toBe('idle')
    expect(apiMock.get).not.toHaveBeenCalled()
  })
})

describe('useCreateItem', () => {
  it('POSTs the payload to the create endpoint', async () => {
    const qc = makeQueryClient()
    const created = makeItem({ id: 'new' })
    apiMock.post.mockResolvedValue(created)

    const { result } = renderHook(() => useCreateItem(), { wrapper: makeWrapper(qc) })

    await result.current.mutateAsync({ name: 'New', description: 'desc' })

    expect(apiMock.post).toHaveBeenCalledWith('/items', { name: 'New', description: 'desc' })
  })

  it('invalidates the items cache after a successful create', async () => {
    const qc = makeQueryClient()
    vi.spyOn(qc, 'invalidateQueries')
    apiMock.post.mockResolvedValue(makeItem({ id: 'new' }))

    // Seed a cached list query so we can observe it being invalidated.
    const seeded = makeItemsResponse([makeItem()])
    qc.setQueryData(queryKeys.items.list(undefined), seeded)

    const { result } = renderHook(() => useCreateItem(), { wrapper: makeWrapper(qc) })

    await result.current.mutateAsync({ name: 'New' })

    expect(qc.invalidateQueries).toHaveBeenCalledWith({ queryKey: queryKeys.items.all })
    expect(qc.getQueryState(queryKeys.items.list(undefined))?.isInvalidated).toBe(true)
  })
})

describe('useUpdateItem', () => {
  it('PATCHes the detail endpoint for the given item id', async () => {
    const qc = makeQueryClient()
    apiMock.patch.mockResolvedValue(makeItem({ id: 'item-1', name: 'Updated' }))

    const { result } = renderHook(() => useUpdateItem('item-1'), { wrapper: makeWrapper(qc) })

    await result.current.mutateAsync({ name: 'Updated' })

    expect(apiMock.patch).toHaveBeenCalledWith('/items/item-1', { name: 'Updated' })
  })

  it('invalidates the items cache after a successful update', async () => {
    const qc = makeQueryClient()
    vi.spyOn(qc, 'invalidateQueries')
    apiMock.patch.mockResolvedValue(makeItem())

    const { result } = renderHook(() => useUpdateItem('item-1'), { wrapper: makeWrapper(qc) })

    await result.current.mutateAsync({ name: 'x' })

    expect(qc.invalidateQueries).toHaveBeenCalledWith({ queryKey: queryKeys.items.all })
  })
})

describe('useDeleteItem', () => {
  it('DELETEs the detail endpoint for the given item id', async () => {
    const qc = makeQueryClient()
    apiMock.delete.mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteItem('item-1'), { wrapper: makeWrapper(qc) })

    await result.current.mutateAsync()

    expect(apiMock.delete).toHaveBeenCalledWith('/items/item-1')
  })

  it('optimistically removes the item from the cache on mutate', async () => {
    const qc = makeQueryClient()
    const cacheKey = queryKeys.items.list({ page: 1, size: 9 })
    qc.setQueryData(
      cacheKey,
      makeItemsResponse([makeItem({ id: 'item-1' }), makeItem({ id: 'item-2' })], { total: 2 }),
    )
    apiMock.delete.mockResolvedValue(undefined)

    const { result } = renderHook(() => useDeleteItem('item-1'), { wrapper: makeWrapper(qc) })

    const promise = result.current.mutateAsync()
    // After onMutate runs (synchronously enqueued), the cache should reflect the optimistic state.
    await waitFor(() => {
      expect(qc.getQueryData<ItemsResponse>(cacheKey)?.items).toHaveLength(1)
      expect(qc.getQueryData<ItemsResponse>(cacheKey)?.items[0].id).toBe('item-2')
    })
    expect(qc.getQueryData<ItemsResponse>(cacheKey)?.total).toBe(1)
    await promise
  })

  it('rolls back the optimistic update when the delete fails', async () => {
    const qc = makeQueryClient()
    const cacheKey = queryKeys.items.list({ page: 1, size: 9 })
    qc.setQueryData(
      cacheKey,
      makeItemsResponse([makeItem({ id: 'item-1' }), makeItem({ id: 'item-2' })], { total: 2 }),
    )
    apiMock.delete.mockRejectedValue(new Error('server boom'))

    const { result } = renderHook(() => useDeleteItem('item-1'), { wrapper: makeWrapper(qc) })

    await expect(result.current.mutateAsync()).rejects.toThrow('server boom')

    await waitFor(() => {
      // onError rollback restores both items and the total.
      expect(qc.getQueryData<ItemsResponse>(cacheKey)?.items).toHaveLength(2)
      expect(qc.getQueryData<ItemsResponse>(cacheKey)?.total).toBe(2)
    })
  })
})

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import type { Item, ItemsResponse } from '@/types/item'

export interface ItemsParams {
  page?: number
  size?: number
  name?: string
  enabled?: boolean
}

export function useItems(params?: ItemsParams) {
  const queryParams = new URLSearchParams()

  if (params?.page) {
    queryParams.append('page', params.page.toString())
  }
  if (params?.size) {
    queryParams.append('size', params.size.toString())
  }
  if (params?.name) {
    queryParams.append('name__ilike', params.name)
  }

  const queryString = queryParams.toString()
  const url = queryString ? `${API.ITEMS.LIST}?${queryString}` : API.ITEMS.LIST

  return useQuery({
    queryKey: queryKeys.items.list(params),
    queryFn: () => api.get<ItemsResponse>(url),
    enabled: params?.enabled ?? true,
  })
}

export interface CreateItemData {
  name: string
  description?: string
}

export function useCreateItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateItemData) => api.post<Item>(API.ITEMS.LIST, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.items.all })
    },
  })
}

export interface UpdateItemData {
  name?: string
  description?: string
}

export function useUpdateItem(itemId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateItemData) => api.patch<Item>(API.ITEMS.DETAIL(itemId), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.items.all })
    },
  })
}

export function useDeleteItem(itemId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => api.delete<void>(API.ITEMS.DETAIL(itemId)),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: queryKeys.items.all })
      const previousItems = queryClient.getQueryData<ItemsResponse>(queryKeys.items.all)

      queryClient.setQueryData<ItemsResponse>(queryKeys.items.all, (old) => {
        if (!old) return old
        return {
          ...old,
          items: old.items.filter((item) => item.id !== itemId),
          total: old.total - 1,
        }
      })

      return { previousItems }
    },
    onError: (_error, _variables, context) => {
      if (context?.previousItems) {
        queryClient.setQueryData(queryKeys.items.all, context.previousItems)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.items.all })
    },
  })
}

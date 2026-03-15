import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import type { Item, ItemsParams, ItemsResponse, CreateItemData, UpdateItemData } from '@/types/item'

export type { CreateItemData, UpdateItemData }

export function useItems(params?: ItemsParams, enabled = true) {
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
    enabled,
  })
}

export function useCreateItem() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateItemData) => api.post<Item>(API.ITEMS.CREATE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.items.all })
    },
  })
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
    mutationFn: () => api.delete(API.ITEMS.DETAIL(itemId)),
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: queryKeys.items.all })
      const previousData = queryClient.getQueriesData<ItemsResponse>({ queryKey: queryKeys.items.all })

      queryClient.setQueriesData<ItemsResponse>({ queryKey: queryKeys.items.all }, (old) => {
        if (!old) return old
        return {
          ...old,
          items: old.items.filter((item) => item.id !== itemId),
          total: old.total - 1,
        }
      })

      return { previousData }
    },
    onError: (_error, _variables, context) => {
      if (context?.previousData) {
        for (const [queryKey, data] of context.previousData) {
          queryClient.setQueryData(queryKey, data)
        }
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.items.all })
    },
  })
}

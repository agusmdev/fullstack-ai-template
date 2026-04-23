import type { ItemsParams } from '@/types/item'

export const API = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
  },
  ITEMS: {
    LIST: '/items',
    CREATE: '/items',
    DETAIL: (id: string) => `/items/${id}`,
  },
} as const

/** Builds the items list URL with query string. Translates semantic params to wire keys (e.g. name → name__ilike). */
export function buildItemsListUrl(params?: ItemsParams): string {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', params.page.toString())
  if (params?.size) queryParams.append('size', params.size.toString())
  if (params?.name) queryParams.append('name__ilike', params.name)
  const queryString = queryParams.toString()
  return queryString ? `${API.ITEMS.LIST}?${queryString}` : API.ITEMS.LIST
}

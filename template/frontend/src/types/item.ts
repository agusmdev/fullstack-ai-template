export interface ItemsParams {
  page?: number
  size?: number
  /** Sent to the API as `name__ilike` for case-insensitive substring match */
  name?: string
}

export interface Item {
  id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  name: string
  description: string | null
  user_id: string
}

export interface ItemsResponse {
  items: Item[]
  total: number
  page?: number
  size?: number
  pages?: number
}

export interface CreateItemData {
  name: string
  description?: string
}

export interface UpdateItemData {
  name?: string
  description?: string
}

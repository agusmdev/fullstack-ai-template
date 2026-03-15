export interface ItemsParams {
  page?: number
  size?: number
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

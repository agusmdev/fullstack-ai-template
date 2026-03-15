import type { ItemsParams } from '@/types/item'

export const queryKeys = {
  items: {
    all: ['items'] as const,
    list: (params?: ItemsParams) => ['items', 'list', params] as const,
  }
}

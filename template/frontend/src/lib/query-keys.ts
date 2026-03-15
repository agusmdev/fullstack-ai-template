import type { ItemsParams } from '@/hooks/useItems'

export const queryKeys = {
  items: {
    all: ['items'] as const,
    list: (params?: ItemsParams) => ['items', 'list', params] as const,
  }
}

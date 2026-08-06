import type { ItemsParams } from '@/types/item'

export const queryKeys = {
  users: {
    all: ['users'] as const,
    me: () => ['users', 'me'] as const,
  },
  items: {
    all: ['items'] as const,
    list: (params?: ItemsParams) => ['items', 'list', params] as const,
  }
}

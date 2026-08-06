import { describe, it, expect } from 'vitest'
import { queryKeys } from './query-keys'

describe('queryKeys', () => {
  describe('users.me', () => {
    it('returns a stable me key', () => {
      expect(queryKeys.users.me()).toEqual(['users', 'me'])
    })

    it('exposes an all key for invalidation', () => {
      expect(queryKeys.users.all).toEqual(['users'])
    })
  })

  describe('items.list', () => {
    it('returns key with no params', () => {
      expect(queryKeys.items.list()).toEqual(['items', 'list', undefined])
    })

    it('returns key with params', () => {
      const params = { page: 1, search: 'test' }
      expect(queryKeys.items.list(params)).toEqual(['items', 'list', params])
    })

    it('includes params in key for cache differentiation', () => {
      const params1 = { page: 1 }
      const params2 = { page: 2 }
      expect(queryKeys.items.list(params1)).not.toEqual(queryKeys.items.list(params2))
    })
  })
})

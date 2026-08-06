import { describe, it, expect } from 'vitest'
import { queryKeys } from './query-keys'

describe('queryKeys', () => {
  describe('users', () => {
    it('returns a stable me key', () => {
      expect(queryKeys.users.me()).toEqual(['users', 'me'])
    })

    it('exposes an all key for invalidation', () => {
      expect(queryKeys.users.all).toEqual(['users'])
    })
  })

  describe('teams', () => {
    it('returns a stable list key', () => {
      expect(queryKeys.teams.list()).toEqual(['teams', 'list'])
    })

    it('exposes an all key for invalidation', () => {
      expect(queryKeys.teams.all).toEqual(['teams'])
    })

    it('list key is stable across calls (same reference shape)', () => {
      expect(queryKeys.teams.list()).toEqual(['teams', 'list'])
    })
  })
})

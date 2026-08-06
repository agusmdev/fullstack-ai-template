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

  describe('workflowStates', () => {
    it('returns a team-scoped list key when a teamId is given', () => {
      expect(queryKeys.workflowStates.list('t-1')).toEqual(['workflowStates', 'list', 't-1'])
    })

    it('falls back to an unscoped list key without a teamId', () => {
      expect(queryKeys.workflowStates.list()).toEqual(['workflowStates', 'list'])
    })

    it('exposes an all key for invalidation', () => {
      expect(queryKeys.workflowStates.all).toEqual(['workflowStates'])
    })
  })

  describe('labels', () => {
    it('returns a team-scoped list key when a teamId is given', () => {
      expect(queryKeys.labels.list('t-1')).toEqual(['labels', 'list', 't-1'])
    })

    it('exposes an all key for invalidation', () => {
      expect(queryKeys.labels.all).toEqual(['labels'])
    })
  })

  describe('issues', () => {
    it('returns a team-scoped list key when a teamId is given', () => {
      expect(queryKeys.issues.list('t-1')).toEqual(['issues', 'list', 't-1'])
    })

    it('returns a detail key for a single issue', () => {
      expect(queryKeys.issues.detail('i-1')).toEqual(['issues', 'detail', 'i-1'])
    })

    it('exposes an all key for invalidation', () => {
      expect(queryKeys.issues.all).toEqual(['issues'])
    })
  })
})

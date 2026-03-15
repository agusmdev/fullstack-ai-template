import { describe, it, expect } from 'vitest'
import { API } from './api-endpoints'

describe('API endpoints', () => {
  describe('AUTH', () => {
    it('has correct login path', () => {
      expect(API.AUTH.LOGIN).toBe('/auth/login')
    })

    it('has correct register path', () => {
      expect(API.AUTH.REGISTER).toBe('/auth/register')
    })

    it('has correct logout path', () => {
      expect(API.AUTH.LOGOUT).toBe('/auth/logout')
    })
  })

  describe('ITEMS', () => {
    it('has correct list path', () => {
      expect(API.ITEMS.LIST).toBe('/items')
    })

    it('generates detail path with id', () => {
      expect(API.ITEMS.DETAIL('abc-123')).toBe('/items/abc-123')
    })

    it('generates detail path with uuid', () => {
      const id = '550e8400-e29b-41d4-a716-446655440000'
      expect(API.ITEMS.DETAIL(id)).toBe(`/items/${id}`)
    })
  })
})

import { describe, it, expect } from 'vitest'
import { API } from './api-endpoints'

describe('API.ITEMS.DETAIL', () => {
  it('interpolates an arbitrary id into the path', () => {
    expect(API.ITEMS.DETAIL('abc-123')).toBe('/items/abc-123')
  })

  it('handles uuid-shaped ids', () => {
    const id = '550e8400-e29b-41d4-a716-446655440000'
    expect(API.ITEMS.DETAIL(id)).toBe(`/items/${id}`)
  })
})

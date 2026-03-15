import { describe, it, expect } from 'vitest'
import { cn } from './utils'

describe('cn', () => {
  it('returns empty string for no args', () => {
    expect(cn()).toBe('')
  })

  it('joins class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar')
  })

  it('merges tailwind conflicts (last wins)', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'skip', 'added')).toBe('base added')
  })

  it('handles undefined and null values', () => {
    expect(cn('a', undefined, null, 'b')).toBe('a b')
  })

  it('handles object syntax', () => {
    expect(cn({ 'text-red-500': true, 'text-blue-500': false })).toBe('text-red-500')
  })

  it('handles array syntax', () => {
    expect(cn(['foo', 'bar'])).toBe('foo bar')
  })

  it('merges conflicting tailwind text sizes', () => {
    expect(cn('text-sm', 'text-lg')).toBe('text-lg')
  })
})

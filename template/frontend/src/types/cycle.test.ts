import { describe, it, expect } from 'vitest'
import {
  cyclePhase,
  formatCycleDate,
  formatCycleWindow,
  computeCycleProgress,
} from './cycle'

describe('cyclePhase', () => {
  it('returns upcoming when today is before start', () => {
    const future = {
      starts_at: '2099-01-01',
      ends_at: '2099-01-14',
    }
    expect(cyclePhase(future)).toBe('upcoming')
  })

  it('returns past when today is after end', () => {
    const past = {
      starts_at: '2000-01-01',
      ends_at: '2000-01-14',
    }
    expect(cyclePhase(past)).toBe('past')
  })

  it('returns active when today is within the window', () => {
    const now = new Date()
    const start = new Date(now)
    start.setDate(start.getDate() - 1)
    const end = new Date(now)
    end.setDate(end.getDate() + 1)
    const active = {
      starts_at: start.toISOString().slice(0, 10),
      ends_at: end.toISOString().slice(0, 10),
    }
    expect(cyclePhase(active)).toBe('active')
  })
})

describe('formatCycleDate', () => {
  it('formats a valid ISO date', () => {
    const result = formatCycleDate('2026-08-01')
    expect(result).not.toBe('—')
    expect(result).toContain('2026')
  })

  it('returns dash for null/undefined', () => {
    expect(formatCycleDate(null)).toBe('—')
    expect(formatCycleDate(undefined)).toBe('—')
  })

  it('returns dash for invalid date', () => {
    expect(formatCycleDate('not-a-date')).toBe('—')
  })
})

describe('formatCycleWindow', () => {
  it('formats start and end dates', () => {
    const result = formatCycleWindow({
      starts_at: '2026-08-01',
      ends_at: '2026-08-14',
    })
    expect(result).toContain('Aug')
    expect(result).toContain('2026')
    expect(result).toContain('–')
  })
})

describe('computeCycleProgress', () => {
  it('counts completed/canceled issues as done', () => {
    const issues = [
      { status_id: 's1' },
      { status_id: 's2' },
      { status_id: 's3' },
    ]
    const types = new Map([
      ['s1', 'completed'],
      ['s2', 'started'],
      ['s3', 'canceled'],
    ])
    const progress = computeCycleProgress(issues, types)
    expect(progress.done).toBe(2)
    expect(progress.total).toBe(3)
  })

  it('returns zero done when no terminal issues', () => {
    const issues = [{ status_id: 's1' }]
    const types = new Map([['s1', 'started']])
    const progress = computeCycleProgress(issues, types)
    expect(progress.done).toBe(0)
    expect(progress.total).toBe(1)
  })

  it('handles empty issues', () => {
    const progress = computeCycleProgress([], new Map())
    expect(progress.done).toBe(0)
    expect(progress.total).toBe(0)
  })
})

import { describe, it, expect } from 'vitest'
import {
  PROJECT_STATUSES,
  DEFAULT_PROJECT_STATUS,
  projectStatusOption,
  isTerminalProjectStatus,
} from './project'

describe('project types & helpers', () => {
  it('default project status is non-terminal (planned) (VAL-PROJECTS-002)', () => {
    expect(DEFAULT_PROJECT_STATUS).toBe('planned')
    const opt = projectStatusOption(DEFAULT_PROJECT_STATUS)
    expect(opt.terminal).toBe(false)
  })

  it('PROJECT_STATUSES includes planned, started, completed, canceled', () => {
    const values = PROJECT_STATUSES.map((s) => s.value)
    expect(values).toEqual(['planned', 'started', 'completed', 'canceled'])
  })

  it('identifies terminal statuses (completed, canceled)', () => {
    expect(isTerminalProjectStatus('completed')).toBe(true)
    expect(isTerminalProjectStatus('canceled')).toBe(true)
    expect(isTerminalProjectStatus('planned')).toBe(false)
    expect(isTerminalProjectStatus('started')).toBe(false)
  })

  it('falls back to Planned for unknown status', () => {
    expect(projectStatusOption('unknown').value).toBe('planned')
  })
})

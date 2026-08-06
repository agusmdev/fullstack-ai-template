import { describe, it, expect } from 'vitest'
import { API } from './api-endpoints'

describe('API.USERS.ME', () => {
  it('points at the authenticated-user profile endpoint', () => {
    expect(API.USERS.ME).toBe('/users/me')
  })
})

describe('API.AUTH', () => {
  it('exposes login, register, and logout endpoints', () => {
    expect(API.AUTH.LOGIN).toBe('/auth/login')
    expect(API.AUTH.REGISTER).toBe('/auth/register')
    expect(API.AUTH.LOGOUT).toBe('/auth/logout')
  })
})

describe('API.TEAMS', () => {
  it('LIST points at the teams collection', () => {
    expect(API.TEAMS.LIST).toBe('/teams')
  })

  it('DETAIL interpolates an arbitrary id into the path', () => {
    expect(API.TEAMS.DETAIL('abc-123')).toBe('/teams/abc-123')
  })

  it('DETAIL handles uuid-shaped ids', () => {
    const id = '550e8400-e29b-41d4-a716-446655440000'
    expect(API.TEAMS.DETAIL(id)).toBe(`/teams/${id}`)
  })
})

describe('API.WORKFLOW_STATES', () => {
  it('LIST points at the workflow-states collection', () => {
    expect(API.WORKFLOW_STATES.LIST).toBe('/workflow-states')
  })
})

describe('API.LABELS', () => {
  it('LIST points at the labels collection', () => {
    expect(API.LABELS.LIST).toBe('/labels')
  })
})

describe('API.ISSUES', () => {
  it('LIST and CREATE point at the issues collection', () => {
    expect(API.ISSUES.LIST).toBe('/issues')
    expect(API.ISSUES.CREATE).toBe('/issues')
  })

  it('DETAIL interpolates an arbitrary id into the path', () => {
    expect(API.ISSUES.DETAIL('issue-9')).toBe('/issues/issue-9')
  })
})

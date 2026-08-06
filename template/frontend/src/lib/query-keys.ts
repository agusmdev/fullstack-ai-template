export const queryKeys = {
  users: {
    all: ['users'] as const,
    me: () => ['users', 'me'] as const,
  },
  teams: {
    all: ['teams'] as const,
    list: () => ['teams', 'list'] as const,
  },
  workflowStates: {
    all: ['workflowStates'] as const,
    list: (teamId?: string) => {
      if (teamId) return ['workflowStates', 'list', teamId] as const
      return ['workflowStates', 'list'] as const
    },
  },
  labels: {
    all: ['labels'] as const,
    list: (teamId?: string) => {
      if (teamId) return ['labels', 'list', teamId] as const
      return ['labels', 'list'] as const
    },
  },
  issues: {
    all: ['issues'] as const,
    list: (teamId?: string) => {
      if (teamId) return ['issues', 'list', teamId] as const
      return ['issues', 'list'] as const
    },
    detail: (id: string) => ['issues', 'detail', id] as const,
  },
}

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
  projects: {
    all: ['projects'] as const,
    list: (teamId?: string) => {
      if (teamId) return ['projects', 'list', teamId] as const
      return ['projects', 'list'] as const
    },
    detail: (id: string) => ['projects', 'detail', id] as const,
  },
  issues: {
    all: ['issues'] as const,
    /**
     * List query key for a team. Pass the serialized params string so distinct
     * filter/search/sort states produce distinct keys (and a bare
     * `list(teamId)` acts as a prefix that matches every variant — used by
     * optimistic updates via `getQueriesData`). Returns a mutable array so it
     * satisfies `useInfiniteQuery`'s `queryKey` type.
     */
    list: (teamId?: string, paramsKey?: string): unknown[] => {
      if (teamId) return ['issues', 'list', teamId, paramsKey ?? '']
      return ['issues', 'list']
    },
    detail: (id: string) => ['issues', 'detail', id] as const,
  },
}

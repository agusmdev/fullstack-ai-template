export const queryKeys = {
  users: {
    all: ['users'] as const,
    me: () => ['users', 'me'] as const,
  },
  teams: {
    all: ['teams'] as const,
    list: () => ['teams', 'list'] as const,
  },
}

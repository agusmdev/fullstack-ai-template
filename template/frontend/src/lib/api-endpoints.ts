export const API = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
  },
  USERS: {
    ME: '/users/me',
  },
  TEAMS: {
    LIST: '/teams',
    DETAIL: (id: string) => `/teams/${id}`,
  },
  WORKFLOW_STATES: {
    LIST: '/workflow-states',
  },
  LABELS: {
    LIST: '/labels',
  },
  PROJECTS: {
    LIST: '/projects',
    CREATE: '/projects',
    DETAIL: (id: string) => `/projects/${id}`,
  },
  CYCLES: {
    LIST: '/cycles',
    CREATE: '/cycles',
    DETAIL: (id: string) => `/cycles/${id}`,
  },
  ISSUES: {
    LIST: '/issues',
    CREATE: '/issues',
    DETAIL: (id: string) => `/issues/${id}`,
    /** Add a label to an issue (idempotent). */
    ADD_LABEL: (id: string, labelId: string) => `/issues/${id}/labels/${labelId}`,
    /** Remove a label from an issue. */
    REMOVE_LABEL: (id: string, labelId: string) => `/issues/${id}/labels/${labelId}`,
  },
} as const

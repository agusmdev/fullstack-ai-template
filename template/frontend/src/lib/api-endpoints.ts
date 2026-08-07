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
  VIEWS: {
    LIST: '/views',
    CREATE: '/views',
    DETAIL: (id: string) => `/views/${id}`,
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
  ISSUE_DEPENDENCIES: {
    LIST: '/issue-dependencies',
    CREATE: '/issue-dependencies',
    DETAIL: (id: string) => `/issue-dependencies/${id}`,
  },
  COMMENTS: {
    LIST: '/comments',
    CREATE: '/comments',
    /** Used for GET / PATCH / DELETE. */
    DETAIL: (id: string) => `/comments/${id}`,
  },
  ACTIVITY: {
    /** Read-only activity feed (list, optionally filtered by issue_id). */
    LIST: '/activity',
    /** Used for GET only — activity is read-only (VAL-ACTIVITY-009). */
    DETAIL: (id: string) => `/activity/${id}`,
  },
} as const

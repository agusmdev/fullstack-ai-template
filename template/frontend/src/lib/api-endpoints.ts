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
} as const

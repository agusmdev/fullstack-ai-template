export const AUTH_TOKEN_KEY = 'auth_token'

// Subscribers are notified whenever the auth token changes — allows api-client
// to trigger AuthContext re-renders when it clears the token on 401.
type AuthChangeListener = () => void
const authChangeListeners = new Set<AuthChangeListener>()

export function subscribeToAuthChanges(listener: AuthChangeListener): () => void {
  authChangeListeners.add(listener)
  return () => authChangeListeners.delete(listener)
}

/** Clear all auth change listeners. For test teardown to prevent state leakage between tests. */
export function clearAllAuthListeners(): void {
  authChangeListeners.clear()
}

function notifyAuthChange() {
  authChangeListeners.forEach(listener => listener())
}

export function getAuthToken(): string | null {
  if (typeof localStorage === 'undefined') {
    return null
  }
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

export function setAuthToken(token: string): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.setItem(AUTH_TOKEN_KEY, token)
  notifyAuthChange()
}

export function isAuthenticated(): boolean {
  return getAuthToken() !== null
}

export function clearAuthToken(): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.removeItem(AUTH_TOKEN_KEY)
  notifyAuthChange()
}

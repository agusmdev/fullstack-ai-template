/**
 * Authentication utilities and global auth manager
 */

export const AUTH_TOKEN_KEY = 'auth_token'

/**
 * Subscribers that should be notified when auth state changes
 * This allows the API client to trigger AuthContext updates when needed
 */
type AuthChangeListener = () => void
const authChangeListeners = new Set<AuthChangeListener>()

/**
 * Subscribe to auth state changes
 * Returns an unsubscribe function
 */
export function subscribeToAuthChanges(listener: AuthChangeListener): () => void {
  authChangeListeners.add(listener)
  return () => authChangeListeners.delete(listener)
}

/**
 * Notify all subscribers that auth state has changed
 */
function notifyAuthChange() {
  authChangeListeners.forEach(listener => listener())
}

/**
 * Get the authentication token from localStorage
 * @returns The auth token or null if not found
 */
export function getAuthToken(): string | null {
  if (typeof localStorage === 'undefined') {
    return null
  }
  return localStorage.getItem(AUTH_TOKEN_KEY)
}

/**
 * Set the authentication token in localStorage
 * @param token - The auth token to store
 */
export function setAuthToken(token: string): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.setItem(AUTH_TOKEN_KEY, token)
  notifyAuthChange()
}

/**
 * Check if the user is authenticated
 * @returns true if the user has a valid token, false otherwise
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null
}

/**
 * Clear the authentication token and notify subscribers
 * This should be called when the user logs out or when a 401 is received
 */
export function clearAuthToken(): void {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.removeItem(AUTH_TOKEN_KEY)
  notifyAuthChange()
}

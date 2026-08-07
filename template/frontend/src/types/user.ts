/** Shape of the backend `GET /users/me` response (UserResponse). */
export interface User {
  id: string
  email: string
  display_name: string
  email_verified_at: string | null
  is_email_verified: boolean
}

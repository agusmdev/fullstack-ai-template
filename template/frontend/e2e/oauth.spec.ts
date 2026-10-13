import {
  test,
  expect,
  BACKEND_URL,
  authHeaders,
  createItem,
  loginUser,
  registerUser,
  storedToken,
} from './fixtures'

// The backend's OAuth callback ends with a redirect to the frontend:
//   success -> /oauth/callback?session=<session id>
//   failure -> /oauth/error?error=<code>
// Google cannot be reached from the tests, so the success case uses a real
// session from the real login API, and the failure case uses a provider the
// backend rejects before it talks to any third party.

test('the callback stores the session and opens the app', async ({ page, api, user }) => {
  const session = await loginUser(api, user.email, user.password)
  await createItem(api, user, { name: 'Made before the OAuth sign-in' })

  await page.goto(`/oauth/callback?session=${encodeURIComponent(session)}`)

  await expect(page).toHaveURL('/')
  await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible()
  expect(await storedToken(page)).toBe(session)
  await page.getByRole('link', { name: 'Items' }).click()
  await expect(page.getByText('Made before the OAuth sign-in')).toBeVisible()
})

test('an OAuth sign-in over another session shows only the new user and ends the old session', async ({
  api,
  user,
  authedPage: page,
}) => {
  await createItem(api, user, { name: 'Owned by the first user' })
  const other = await registerUser(api)
  await createItem(api, other, { name: 'Owned by the second user' })
  await page.goto('/items')
  await expect(page.getByText('Owned by the first user')).toBeVisible()

  await page.goto(`/oauth/callback?session=${encodeURIComponent(other.token)}`)

  await expect(page).toHaveURL('/')
  expect(await storedToken(page)).toBe(other.token)
  await page.getByRole('link', { name: 'Items' }).click()
  await expect(page.getByText('Owned by the second user')).toBeVisible()
  await expect(page.getByText('Owned by the first user')).toHaveCount(0)
  // The replaced session is revoked on the server, not only forgotten.
  await expect
    .poll(async () => (await api.get('/items', { headers: authHeaders(user) })).status())
    .toBe(401)
})

test('the callback without a session shows the error page', async ({ page }) => {
  await page.goto('/oauth/callback')

  await expect(page).toHaveURL('/oauth/error?error=missing_session')
  await expect(page.getByText('The sign-in response did not include a session.')).toBeVisible()
  expect(await storedToken(page)).toBeNull()
})

test('a backend OAuth failure lands on the error page with a way back', async ({ page }) => {
  await page.goto(`${BACKEND_URL}/auth/oauth/unknown-provider/callback?code=anything`)

  await expect(page).toHaveURL('/oauth/error?error=unsupported_provider')
  await expect(page.getByText('Sign-in failed')).toBeVisible()
  await expect(page.getByText('This sign-in provider is not supported.')).toBeVisible()
  await page.getByRole('link', { name: 'Back to sign in' }).click()
  await expect(page).toHaveURL('/login')
})

test('a user who declines consent at the provider lands on the error page', async ({ page }) => {
  // What the provider sends back when the user clicks "Cancel": no code, an error.
  await page.goto(`${BACKEND_URL}/auth/oauth/google/callback?error=access_denied`)

  await expect(page).toHaveURL('/oauth/error?error=access_denied')
  await expect(page.getByText('Sign-in was cancelled at the provider.')).toBeVisible()
})

test('the error page explains unknown error codes', async ({ page }) => {
  await page.goto('/oauth/error?error=something_new')

  await expect(page.getByText('Something went wrong while signing you in.')).toBeVisible()
  await expect(page.getByText('something_new')).toBeVisible()
})

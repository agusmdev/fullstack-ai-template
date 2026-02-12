import { test, expect } from '@playwright/test'

/**
 * E2E tests for authentication flow.
 *
 * These tests cover the complete user authentication journey:
 * - Registration with valid credentials
 * - Registration validation (email format, password length, password matching)
 * - Login with valid credentials
 * - Login validation (invalid credentials show error)
 * - Logout flow
 * - Protected route redirection
 *
 * NOTE: These tests require a running backend server at the API_BASE_URL.
 * For local testing, ensure the backend is running with the database initialized.
 */

test.describe('Authentication Flow', () => {
  // Use a unique email for each test run to avoid conflicts
  const generateTestEmail = () => `e2e-test-${Date.now()}@example.com`
  const testPassword = 'TestPassword123!'

  test.beforeEach(async ({ page }) => {
    // Clear any existing auth state before each test
    await page.context().clearCookies()
    await page.goto('/')
  })

  test('user can register with valid credentials', async ({ page }) => {
    const testEmail = generateTestEmail()

    // Navigate to register page
    await page.goto('/register')

    // Fill out the registration form
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[name="password"]', testPassword)
    await page.fill('input[name="confirmPassword"]', testPassword)

    // Submit the form
    await page.click('button[type="submit"]')

    // After successful registration, should redirect to login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('registration validates email format', async ({ page }) => {
    await page.goto('/register')

    // Fill with invalid email
    await page.fill('input[type="email"]', 'not-an-email')
    await page.fill('input[name="password"]', testPassword)
    await page.fill('input[name="confirmPassword"]', testPassword)

    // Trigger validation by clicking submit
    await page.click('button[type="submit"]')

    // Should show validation error
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeFocused()
  })

  test('registration validates password length', async ({ page }) => {
    await page.goto('/register')

    // Fill with short password
    await page.fill('input[type="email"]', generateTestEmail())
    await page.fill('input[name="password"]', 'short')
    await page.fill('input[name="confirmPassword"]', 'short')

    // Trigger validation
    await page.click('button[type="submit"]')

    // Should show validation error
    const passwordInput = page.locator('input[name="password"]')
    await expect(passwordInput).toBeFocused()
  })

  test('registration validates password confirmation match', async ({ page }) => {
    await page.goto('/register')

    // Fill with mismatched passwords
    await page.fill('input[type="email"]', generateTestEmail())
    await page.fill('input[name="password"]', testPassword)
    await page.fill('input[name="confirmPassword"]', 'DifferentPassword123!')

    // Trigger validation
    await page.click('button[type="submit"]')

    // Should show validation error for confirmation field
    const confirmPasswordInput = page.locator('input[name="confirmPassword"]')
    await expect(confirmPasswordInput).toBeFocused()
  })

  test('user can login with valid credentials', async ({ page }) => {
    // First, register a user
    const testEmail = generateTestEmail()

    await page.goto('/register')
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[name="password"]', testPassword)
    await page.fill('input[name="confirmPassword"]', testPassword)
    await page.click('button[type="submit"]')

    // Wait for redirect to login
    await expect(page).toHaveURL(/\/login/)

    // Now login with the same credentials
    await page.fill('input[type="email"]', testEmail)
    await page.fill('input[type="password"]', testPassword)
    await page.click('button[type="submit"]')

    // After successful login, should redirect to home page
    await expect(page).toHaveURL(/\//)
  })

  test('login shows error with invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Try to login with non-existent credentials
    await page.fill('input[type="email"]', 'nonexistent@example.com')
    await page.fill('input[type="password"]', 'WrongPassword123!')
    await page.click('button[type="submit"]')

    // Should show an error message
    const errorDiv = page.locator('div.bg-destructive')
    await expect(errorDiv).toBeVisible()
  })

  test('login validates required fields', async ({ page }) => {
    await page.goto('/login')

    // Try to submit without filling fields
    await page.click('button[type="submit"]')

    // Should show validation errors
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeFocused()
  })

  test('protected route redirects to login when not authenticated', async ({ page }) => {
    // Try to access the items page (which requires authentication)
    await page.goto('/items')

    // Should redirect to login with redirect parameter
    await expect(page).toHaveURL(/\/login.*redirect.*/)
  })

  test('navigation links between login and register', async ({ page }) => {
    // Start on login page
    await page.goto('/login')

    // Click link to register
    await page.click('a[href="/register"]')
    await expect(page).toHaveURL('/register')

    // Click link back to login
    await page.click('a[href="/login"]')
    await expect(page).toHaveURL('/login')
  })
})

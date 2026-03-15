import { test, expect } from '@playwright/test'

/**
 * E2E tests for Items CRUD flow.
 *
 * These tests cover the complete items management lifecycle:
 * - Creating a new item
 * - Reading (viewing) items list
 * - Updating an existing item
 * - Deleting an item
 * - Searching/filtering items
 * - Pagination
 *
 * NOTE: These tests require a running backend server and authenticated user.
 */

test.describe('Items CRUD Flow', () => {
  const generateTestEmail = () => `e2e-items-${Date.now()}@example.com`
  const testPassword = 'TestPassword123!'

  // Helper function to authenticate user
  async function authenticateUser(page: any, email: string, password: string) {
    await page.goto('/register')
    await page.fill('input[type="email"]', email)
    await page.fill('input[name="password"]', password)
    await page.fill('input[name="confirmPassword"]', password)
    await page.click('button[type="submit"]')

    // Register redirects to home on success
    await expect(page).toHaveURL('/')
  }

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies()

    const testEmail = generateTestEmail()
    await authenticateUser(page, testEmail, testPassword)
  })

  test('displays empty state when no items exist', async ({ page }) => {
    await page.goto('/items')

    // Should show empty state message
    await expect(page.locator('text=No items yet')).toBeVisible()
    await expect(page.locator('text=Get started by creating your first item')).toBeVisible()
  })

  test('can create a new item with title only', async ({ page }) => {
    await page.goto('/items')

    // Click the Create Item button
    await page.click('button:has-text("Create Item")')

    // Wait for dialog to open
    await expect(page.locator('text=Create New Item')).toBeVisible()

    // Fill in the title
    await page.fill('input[placeholder="Enter item name"]', 'E2E Test Item')

    // Submit the form
    await page.click('button:has-text("Create")')

    // Wait for dialog to close and item to appear
    await expect(page.locator('text=E2E Test Item')).toBeVisible()
  })

  test('can create a new item with title and description', async ({ page }) => {
    await page.goto('/items')

    // Click the Create Item button
    await page.click('button:has-text("Create Item")')

    // Fill in both title and description
    await page.fill('input[placeholder="Enter item name"]', 'Item with Description')
    await page.fill('textarea[placeholder="Enter item description"]', 'This is a test description')

    // Submit the form
    await page.click('button:has-text("Create")')

    // Wait for item to appear
    await expect(page.locator('text=Item with Description')).toBeVisible()
    await expect(page.locator('text=This is a test description')).toBeVisible()
  })

  test('can create multiple items and see them in the list', async ({ page }) => {
    await page.goto('/items')

    // Create first item
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'First Item')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=First Item')).toBeVisible()

    // Create second item
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Second Item')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=Second Item')).toBeVisible()

    // Check the count
    await expect(page.locator('text=2 items total')).toBeVisible()
  })

  test('create dialog validates required title field', async ({ page }) => {
    await page.goto('/items')

    // Click the Create Item button
    await page.click('button:has-text("Create Item")')

    // Try to submit without filling title
    await page.click('button:has-text("Create")')

    // Should show validation error
    const titleInput = page.locator('input[placeholder="Enter item name"]')
    await expect(titleInput).toBeFocused()
  })

  test('can cancel item creation', async ({ page }) => {
    await page.goto('/items')

    // Click the Create Item button
    await page.click('button:has-text("Create Item")')

    // Fill in some data
    await page.fill('input[placeholder="Enter item name"]', 'Cancelled Item')

    // Click Cancel
    await page.click('button:has-text("Cancel")')

    // Dialog should close and item should not appear
    await expect(page.locator('text=Cancelled Item')).not.toBeVisible()
  })

  test('can edit an existing item', async ({ page }) => {
    await page.goto('/items')

    // Create an item first
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Original Title')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=Original Title')).toBeVisible()

    // Find and click the edit button for the item
    const itemCard = page.getByTestId('item-card').filter({ hasText: 'Original Title' })
    await itemCard.locator('button:has([data-lucide="pencil"])').click()

    // Wait for edit dialog
    await expect(page.locator('text=Edit Item')).toBeVisible()

    // Update the title
    const titleInput = page.locator('input[placeholder="Enter item name"]')
    await titleInput.fill('')
    await titleInput.fill('Updated Title')

    // Submit the form
    await page.click('button:has-text("Update")')

    // Verify the item was updated
    await expect(page.locator('text=Updated Title')).toBeVisible()
    await expect(page.locator('text=Original Title')).not.toBeVisible()
  })

  test('can edit an item with description', async ({ page }) => {
    await page.goto('/items')

    // Create an item with description
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Item to Edit')
    await page.fill('textarea[placeholder="Enter item description"]', 'Original description')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=Item to Edit')).toBeVisible()

    // Edit the item
    const itemCard = page.getByTestId('item-card').filter({ hasText: 'Item to Edit' })
    await itemCard.locator('button:has([data-lucide="pencil"])').click()

    // Update description
    const descInput = page.locator('textarea[placeholder="Enter item description"]')
    await descInput.fill('')
    await descInput.fill('Updated description')

    // Submit the form
    await page.click('button:has-text("Update")')

    // Verify the description was updated
    await expect(page.locator('text=Updated description')).toBeVisible()
  })

  test('can cancel item editing', async ({ page }) => {
    await page.goto('/items')

    // Create an item
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Keep Original')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=Keep Original')).toBeVisible()

    // Start editing
    const itemCard = page.getByTestId('item-card').filter({ hasText: 'Keep Original' })
    await itemCard.locator('button:has([data-lucide="pencil"])').click()

    // Change the title but cancel
    await page.fill('input[placeholder="Enter item name"]', 'Changed Title')
    await page.click('button:has-text("Cancel")')

    // Original title should remain
    await expect(page.locator('text=Keep Original')).toBeVisible()
    await expect(page.locator('text=Changed Title')).not.toBeVisible()
  })

  test('can delete an item', async ({ page }) => {
    await page.goto('/items')

    // Create an item
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'To Be Deleted')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=To Be Deleted')).toBeVisible()

    // Click the delete button
    const itemCard = page.getByTestId('item-card').filter({ hasText: 'To Be Deleted' })
    await itemCard.locator('button:has([data-lucide="trash-2"])').click()

    // Confirm deletion in alert dialog
    await expect(page.locator('text=Are you sure you want to delete "To Be Deleted"?')).toBeVisible()
    await page.click('button:has-text("Delete")')

    // Item should be removed
    await expect(page.locator('text=To Be Deleted')).not.toBeVisible()
    await expect(page.locator('text=No items yet')).toBeVisible()
  })

  test('can cancel item deletion', async ({ page }) => {
    await page.goto('/items')

    // Create an item
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Keep This Item')
    await page.click('button:has-text("Create")')
    await expect(page.locator('text=Keep This Item')).toBeVisible()

    // Click delete but cancel
    const itemCard = page.getByTestId('item-card').filter({ hasText: 'Keep This Item' })
    await itemCard.locator('button:has([data-lucide="trash-2"])').click()

    // Click Cancel in the alert dialog
    await page.click('button:has-text("Cancel")')

    // Item should still be there
    await expect(page.locator('text=Keep This Item')).toBeVisible()
  })

  test('can search items by title', async ({ page }) => {
    await page.goto('/items')

    // Create multiple items
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Apple')
    await page.click('button:has-text("Create")')

    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Banana')
    await page.click('button:has-text("Create")')

    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Cherry')
    await page.click('button:has-text("Create")')

    // Wait for all items to appear
    await expect(page.locator('text=3 items total')).toBeVisible()

    // Search for "App" — search is debounced on input, no button needed
    await page.fill('input[placeholder="Search items by name..."]', 'App')
    await page.waitForTimeout(400)

    // Should only show Apple
    await expect(page.locator('text=Apple')).toBeVisible()
    await expect(page.locator('text=Banana')).not.toBeVisible()
    await expect(page.locator('text=Cherry')).not.toBeVisible()
  })

  test('can clear search', async ({ page }) => {
    await page.goto('/items')

    // Create items
    await page.click('button:has-text("Create Item")')
    await page.fill('input[placeholder="Enter item name"]', 'Searchable Item')
    await page.click('button:has-text("Create")')

    // Search — debounced on input
    await page.fill('input[placeholder="Search items by name..."]', 'Search')
    await page.waitForTimeout(400)

    await expect(page.locator('text=Searchable Item')).toBeVisible()

    // Clear search
    await page.click('button:has-text("Clear")')

    // Search input should be empty and Clear button should be gone
    const searchInput = page.locator('input[placeholder="Search items by name..."]')
    await expect(searchInput).toHaveValue('')
  })

  test('shows pagination controls when items exceed page size', async ({ page }) => {
    await page.goto('/items')

    // Create more than 9 items (page size is 9)
    for (let i = 1; i <= 12; i++) {
      await page.click('button:has-text("Create Item")')
      await page.fill('input[placeholder="Enter item name"]', `Item ${i}`)
      await page.click('button:has-text("Create")')
      await expect(page.locator(`text=Item ${i}`)).toBeVisible()
    }

    // Should show pagination controls
    await expect(page.locator('text=Page 1 of 2')).toBeVisible()
    await expect(page.locator('button:has-text("Next")')).toBeVisible()

    // Navigate to next page
    await page.click('button:has-text("Next")')

    // Should be on page 2
    await expect(page.locator('text=Page 2 of 2')).toBeVisible()
    await expect(page.locator('button:has-text("Previous")')).toBeVisible()
  })
})

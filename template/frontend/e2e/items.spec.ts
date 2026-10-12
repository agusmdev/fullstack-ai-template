import {
  type Page,
  test,
  expect,
  authHeaders,
  createItem,
  createItems,
  errorToast,
  listItems,
  registerUser,
} from './fixtures'

const PAGE_SIZE = 9 // the items page shows 9 items per page

function itemCard(page: Page, name: string) {
  return page.getByTestId('item-card').filter({ has: page.getByText(name, { exact: true }) })
}

function searchBox(page: Page) {
  return page.getByPlaceholder('Search items by name...')
}

async function openItemsPage(page: Page) {
  await page.goto('/items')
  await expect(page.getByRole('heading', { name: 'Items' })).toBeVisible()
}

test('a new user sees the empty state', async ({ authedPage: page }) => {
  await openItemsPage(page)
  await expect(page.getByText('No items yet')).toBeVisible()
  await expect(page.getByText('Get started by creating your first item.')).toBeVisible()
  await expect(page.getByText('No items found')).toBeVisible()
})

test('creates an item through the dialog', async ({ authedPage: page, api, user }) => {
  await openItemsPage(page)
  await page.getByRole('button', { name: 'Create Item' }).click()
  const dialog = page.getByRole('dialog', { name: 'Create New Item' })
  await dialog.getByLabel('Name').fill('Groceries')
  await dialog.getByLabel('Description (Optional)').fill('Milk, eggs, bread')
  await dialog.getByRole('button', { name: 'Create', exact: true }).click()

  await expect(dialog).toBeHidden()
  await expect(itemCard(page, 'Groceries')).toContainText('Milk, eggs, bread')
  await expect(page.getByText('1 item total')).toBeVisible()
  const saved = await listItems(api, user)
  expect(saved.map(({ name, description }) => ({ name, description }))).toEqual([
    { name: 'Groceries', description: 'Milk, eggs, bread' },
  ])
})

test('the create dialog requires a name and can be cancelled', async ({
  authedPage: page,
  api,
  user,
}) => {
  await openItemsPage(page)
  await page.getByRole('button', { name: 'Create Item' }).click()
  const dialog = page.getByRole('dialog', { name: 'Create New Item' })
  await dialog.getByRole('button', { name: 'Create', exact: true }).click()
  await expect(dialog.getByText('Name is required')).toBeVisible()

  await dialog.getByLabel('Name').fill('Not wanted')
  await dialog.getByRole('button', { name: 'Cancel' }).click()
  await expect(dialog).toBeHidden()
  await expect(page.getByText('No items yet')).toBeVisible()
  expect(await listItems(api, user)).toEqual([])
})

test('edits an item', async ({ authedPage: page, api, user }) => {
  const item = await createItem(api, user, { name: 'Draft', description: 'First version' })
  await openItemsPage(page)

  await page.getByRole('button', { name: 'Edit Draft', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Edit Item' })
  await expect(dialog.getByLabel('Name')).toHaveValue('Draft')
  await expect(dialog.getByLabel('Description (Optional)')).toHaveValue('First version')
  await dialog.getByLabel('Name').fill('Final')
  await dialog.getByLabel('Description (Optional)').fill('Second version')
  await dialog.getByRole('button', { name: 'Update' }).click()

  await expect(dialog).toBeHidden()
  await expect(itemCard(page, 'Final')).toContainText('Second version')
  await expect(itemCard(page, 'Draft')).toHaveCount(0)
  const response = await api.get(`/items/${item.id}`, { headers: authHeaders(user) })
  expect(await response.json()).toMatchObject({ name: 'Final', description: 'Second version' })
})

test('clears an item description', async ({ authedPage: page, api, user }) => {
  const item = await createItem(api, user, { name: 'Notes', description: 'Remove me' })
  await openItemsPage(page)
  await expect(itemCard(page, 'Notes')).toContainText('Remove me')

  await page.getByRole('button', { name: 'Edit Notes', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Edit Item' })
  await dialog.getByLabel('Description (Optional)').fill('')
  await dialog.getByRole('button', { name: 'Update' }).click()

  await expect(dialog).toBeHidden()
  await expect(itemCard(page, 'Notes')).not.toContainText('Remove me')
  const response = await api.get(`/items/${item.id}`, { headers: authHeaders(user) })
  expect(await response.json()).toMatchObject({ name: 'Notes', description: null })
})

test('deletes an item only after confirmation', async ({ authedPage: page, api, user }) => {
  const [keep, remove] = await createItems(api, user, ['Keep me', 'Delete me'])
  await openItemsPage(page)

  await page.getByRole('button', { name: 'Delete Delete me', exact: true }).click()
  const confirm = page.getByRole('alertdialog', { name: 'Delete Item' })
  await expect(confirm).toContainText('Are you sure you want to delete "Delete me"?')
  await confirm.getByRole('button', { name: 'Cancel' }).click()
  await expect(confirm).toBeHidden()
  await expect(itemCard(page, 'Delete me')).toBeVisible()

  await page.getByRole('button', { name: 'Delete Delete me', exact: true }).click()
  await confirm.getByRole('button', { name: 'Delete' }).click()

  await expect(confirm).toBeHidden()
  await expect(itemCard(page, 'Delete me')).toHaveCount(0)
  await expect(itemCard(page, 'Keep me')).toBeVisible()
  await expect(page.getByText('1 item total')).toBeVisible()
  expect((await listItems(api, user)).map(item => item.id)).toEqual([keep.id])
  const gone = await api.get(`/items/${remove.id}`, { headers: authHeaders(user) })
  expect(gone.status()).toBe(404)
})

test('searches by name on the backend, ignoring case', async ({ authedPage: page, api, user }) => {
  await createItems(api, user, ['Apple pie', 'Banana bread', 'Pineapple juice'])
  await openItemsPage(page)
  await expect(page.getByTestId('item-card')).toHaveCount(3)

  // Typed one key at a time, slower than the search debounce, like a real user.
  await searchBox(page).pressSequentially('APPLE', { delay: 350 })
  await expect(searchBox(page)).toHaveValue('APPLE')
  await expect(searchBox(page)).toBeFocused()
  await expect(page.getByText('2 items total')).toBeVisible()
  await expect(itemCard(page, 'Apple pie')).toBeVisible()
  await expect(itemCard(page, 'Pineapple juice')).toBeVisible()
  await expect(itemCard(page, 'Banana bread')).toHaveCount(0)

  await searchBox(page).fill('no such thing')
  await expect(page.getByText('No matching items')).toBeVisible()
  await expect(page.getByTestId('item-card')).toHaveCount(0)

  await page.getByRole('button', { name: 'Clear' }).click()
  await expect(searchBox(page)).toHaveValue('')
  await expect(page.getByTestId('item-card')).toHaveCount(3)
})

test('search treats % and _ as plain characters', async ({ authedPage: page, api, user }) => {
  await createItems(api, user, ['A_B', 'AxB', '100%', '1000'])
  await openItemsPage(page)
  await expect(page.getByTestId('item-card')).toHaveCount(4)

  await searchBox(page).fill('_')
  await expect(page.getByText('1 item total')).toBeVisible()
  await expect(itemCard(page, 'A_B')).toBeVisible()
  await expect(page.getByTestId('item-card')).toHaveCount(1)

  await searchBox(page).fill('0%')
  await expect(itemCard(page, '100%')).toBeVisible()
  await expect(page.getByTestId('item-card')).toHaveCount(1)
})

test('paginates the list', async ({ authedPage: page, api, user }) => {
  const names = Array.from(
    { length: PAGE_SIZE + 3 },
    (_, i) => `Item ${String(i + 1).padStart(2, '0')}`
  )
  await createItems(api, user, names)
  await openItemsPage(page)

  const pagination = page.getByRole('navigation', { name: 'Pagination' })
  const previous = pagination.getByRole('button', { name: 'Go to previous page' })
  const next = pagination.getByRole('button', { name: 'Go to next page' })
  await expect(page.getByText(`${names.length} items total`)).toBeVisible()
  await expect(pagination).toContainText('Page 1 of 2')
  await expect(page.getByTestId('item-card')).toHaveCount(PAGE_SIZE)
  await expect(itemCard(page, 'Item 01')).toBeVisible()
  await expect(previous).toBeDisabled()

  await next.click()
  await expect(pagination).toContainText('Page 2 of 2')
  await expect(page.getByTestId('item-card')).toHaveCount(3)
  await expect(itemCard(page, 'Item 12')).toBeVisible()
  await expect(itemCard(page, 'Item 01')).toHaveCount(0)
  await expect(next).toBeDisabled()

  await previous.click()
  await expect(pagination).toContainText('Page 1 of 2')
  await expect(itemCard(page, 'Item 01')).toBeVisible()
})

test('deleting the last item of a page goes back to the last page with items', async ({
  authedPage: page,
  api,
  user,
}) => {
  const names = Array.from(
    { length: PAGE_SIZE + 1 },
    (_, i) => `Item ${String(i + 1).padStart(2, '0')}`
  )
  await createItems(api, user, names)
  await openItemsPage(page)

  const pagination = page.getByRole('navigation', { name: 'Pagination' })
  await pagination.getByRole('button', { name: 'Go to next page' }).click()
  await expect(pagination).toContainText('Page 2 of 2')
  await expect(page.getByTestId('item-card')).toHaveCount(1)

  await page.getByRole('button', { name: 'Delete Item 10', exact: true }).click()
  await page
    .getByRole('alertdialog', { name: 'Delete Item' })
    .getByRole('button', { name: 'Delete' })
    .click()

  await expect(page.getByText(`${PAGE_SIZE} items total`)).toBeVisible()
  await expect(page.getByTestId('item-card')).toHaveCount(PAGE_SIZE)
  await expect(itemCard(page, 'Item 01')).toBeVisible()
  await expect(page.getByText('No items yet')).toHaveCount(0)
})

test('a new search starts again at page 1', async ({ authedPage: page, api, user }) => {
  // 20 items: 3 pages. "Item 1" matches Item 10 to Item 19: 2 pages.
  const names = Array.from({ length: 20 }, (_, i) => `Item ${String(i + 1).padStart(2, '0')}`)
  await createItems(api, user, names)
  await openItemsPage(page)

  const pagination = page.getByRole('navigation', { name: 'Pagination' })
  await pagination.getByRole('button', { name: 'Go to next page' }).click()
  await expect(pagination).toContainText('Page 2 of 3')
  await expect(itemCard(page, 'Item 10')).toBeVisible()

  await searchBox(page).fill('Item 1')
  await expect(page.getByText('10 items total')).toBeVisible()
  await expect(pagination).toContainText('Page 1 of 2')
  await expect(page.getByTestId('item-card')).toHaveCount(PAGE_SIZE)
  await expect(itemCard(page, 'Item 10')).toBeVisible()
  await expect(itemCard(page, 'Item 19')).toHaveCount(0)
})

test('users never see each other’s items', async ({ authedPage: page, api, user, loginAs }) => {
  const otherUser = await registerUser(api)
  const theirs = await createItem(api, otherUser, { name: 'Their secret' })
  await createItem(api, user, { name: 'Mine' })

  await openItemsPage(page)
  await expect(itemCard(page, 'Mine')).toBeVisible()
  await expect(page.getByText('Their secret')).toHaveCount(0)
  await expect(page.getByText('1 item total')).toBeVisible()

  const otherPage = await loginAs(otherUser)
  await openItemsPage(otherPage)
  await expect(itemCard(otherPage, 'Their secret')).toBeVisible()
  await expect(otherPage.getByText('Mine', { exact: true })).toHaveCount(0)

  // The backend refuses direct access to another user's item too.
  const headers = authHeaders(user)
  expect((await api.get(`/items/${theirs.id}`, { headers })).status()).toBe(404)
  const patch = await api.patch(`/items/${theirs.id}`, { headers, data: { name: 'Hacked' } })
  expect(patch.status()).toBe(404)
  expect((await api.delete(`/items/${theirs.id}`, { headers })).status()).toBe(404)
  expect((await listItems(api, otherUser)).map(item => item.name)).toEqual(['Their secret'])
})

test.describe('backend errors show as a toast', () => {
  // The item is deleted on the backend (say, from another device) while the
  // page still shows it. The next change gets a real 404.

  test('when an update fails', async ({ authedPage: page, api, user }) => {
    const item = await createItem(api, user, { name: 'Stale' })
    await openItemsPage(page)
    await expect(itemCard(page, 'Stale')).toBeVisible()
    await api.delete(`/items/${item.id}`, { headers: authHeaders(user) })

    await page.getByRole('button', { name: 'Edit Stale', exact: true }).click()
    const dialog = page.getByRole('dialog', { name: 'Edit Item' })
    await dialog.getByLabel('Name').fill('Renamed')
    const responsePromise = page.waitForResponse(r => r.url().endsWith(`/items/${item.id}`))
    await dialog.getByRole('button', { name: 'Update' }).click()

    const response = await responsePromise
    expect(response.status()).toBe(404)
    const { detail } = await response.json()
    await expect(errorToast(page)).toContainText('Failed to update item')
    await expect(errorToast(page)).toContainText(detail)
    await expect(dialog).toBeVisible() // the user keeps what they typed
  })

  test('when a delete fails', async ({ authedPage: page, api, user }) => {
    const item = await createItem(api, user, { name: 'Stale' })
    await openItemsPage(page)
    await expect(itemCard(page, 'Stale')).toBeVisible()
    await api.delete(`/items/${item.id}`, { headers: authHeaders(user) })

    await page.getByRole('button', { name: 'Delete Stale', exact: true }).click()
    const responsePromise = page.waitForResponse(r => r.url().endsWith(`/items/${item.id}`))
    await page
      .getByRole('alertdialog', { name: 'Delete Item' })
      .getByRole('button', { name: 'Delete' })
      .click()

    const response = await responsePromise
    expect(response.status()).toBe(404)
    const { detail } = await response.json()
    await expect(errorToast(page)).toContainText('Failed to delete item')
    await expect(errorToast(page)).toContainText(detail)
    // The optimistic removal is rolled back, then the list reloads from the
    // backend, where the item is already gone: the page and the backend agree.
    await expect(page.getByText('No items yet')).toBeVisible()
    await expect(page.getByTestId('item-card')).toHaveCount(0)
    expect(await listItems(api, user)).toEqual([])
  })
})

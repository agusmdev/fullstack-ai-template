# E2E testing

This project has **end-to-end tests only**. There are no unit tests and no
mocks, fakes, patches, dependency overrides, network interception, fake clocks,
in-process apps or SQLite. Guards fail the run when someone adds one.

Every new feature, endpoint, page or module gets e2e tests in the same change.

| Suite | Where tests go | Run (from project root) | Needs |
|---|---|---|---|
| Backend API | `backend/tests/e2e/test_<feature>.py` | `make test-backend` | Docker, uv |
| Full stack (browser) | `frontend/e2e/<feature>.spec.ts` | `make test-e2e` | Docker, uv, bun, Chromium |
| Both | | `make test` | all of the above |

---

## Backend suite

### How the stack starts

Run `cd backend && uv run pytest` (or `make test`; `make test-cov` adds a
coverage report that includes the server process). No `.env` and no running
database are needed. Per session:

1. testcontainers starts Postgres with the `db` image from `docker-compose.yml`.
2. `alembic upgrade head`, then `alembic check` (Guard 3).
3. The real app starts in a child process:
   `uvicorn --factory app.main:create_app` on 127.0.0.1, free port, settings
   from env vars only (`LOG_FORMAT=json`, `ENVIRONMENT=local` so Sentry is off,
   Google endpoints point at a closed local port). `tests/e2e/run_server.py`
   stops the server if pytest dies.
4. Before **each** test, every application table is truncated. Tests pass in
   any order.

If the stack cannot start, the run stops with one message.

Code: `tests/e2e/stack.py`, fixtures in `tests/e2e/conftest.py` (read its
docstring first), guard hooks in `tests/conftest.py`, guard logic in
`tests/e2e/guards.py`.

### Fixtures (`tests/e2e/conftest.py`)

| Fixture | What |
|---|---|
| `api` | anonymous `httpx.Client` for the live server |
| `auth_client` | client of a new registered and logged-in user |
| `register_user(email=..., password=..., display_name=...)` | returns `RegisteredUser` (`.client`, `.id`, `.email`, `.password`, `.display_name`, `.session_id`) |
| `make_client(token=None)` | a new client, with a Bearer token if given |
| `server_log` | server output of this test: `.wide_event_for(response)`, `.events()`, `.lines()`, `.text()`, `.wait_for(...)` |
| `db` | raw SQL (`.execute`, `.fetch_one`, `.fetch_all`): **only** for state no endpoint can create |
| `server` | (session) the live server: `.base_url`, `.log` |

Helpers (`tests/e2e/helpers.py`): `assert_error(response, status, error_code, detail=None)`,
`create_item`, `login`, `unique_email`, `password_reset_token`,
`email_verification_token`, `deactivate_user`, `create_passwordless_user`,
`drop_server_connections(db, client)`, a context manager (`with drop_server_connections(db, client): response = client.get(...)`) that simulates a database outage until the block ends, then waits until the server's pool works again, constants
`DEFAULT_PASSWORD`, `EXPIRED`, `NUL`. Put a `create_<entity>` helper here for
each new resource.

### Worked example: tests for a new `notes` resource

`tests/e2e/helpers.py`:

```python
def create_note(
    client: httpx.Client, name: str = "Note", description: str | None = None
) -> dict[str, Any]:
    """Create a note through POST /notes and return the response body."""
    payload: dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    response = client.post("/notes", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
```

`tests/e2e/test_notes.py`:

```python
"""Notes CRUD and ownership."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.e2e.helpers import assert_error, create_note

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import ServerLogView


def test_create_then_get(auth_client: httpx.Client) -> None:
    response = auth_client.post("/notes", json={"name": "Groceries"})

    assert response.status_code == 201
    note = response.json()
    assert auth_client.get(f"/notes/{note['id']}").json() == note


def test_rename(auth_client: httpx.Client, server_log: ServerLogView) -> None:
    note = create_note(auth_client, name="Old")

    response = auth_client.patch(f"/notes/{note['id']}", json={"name": "New"})

    assert response.status_code == 200
    assert auth_client.get(f"/notes/{note['id']}").json()["name"] == "New"
    assert server_log.wide_event_for(response)["action"] == "update"


def test_delete(auth_client: httpx.Client) -> None:
    note = create_note(auth_client)

    assert auth_client.delete(f"/notes/{note['id']}").status_code == 204
    assert_error(auth_client.get(f"/notes/{note['id']}"), 404, "not_found")


def test_list_is_paged(auth_client: httpx.Client) -> None:
    for name in ("A", "B", "C"):
        create_note(auth_client, name=name)

    page = auth_client.get("/notes", params={"size": 2, "page": 2}).json()

    assert [n["name"] for n in page["items"]] == ["C"]
    assert (page["total"], page["pages"]) == (3, 2)


def test_empty_name_is_rejected(auth_client: httpx.Client) -> None:
    response = auth_client.post("/notes", json={"name": ""})

    body = assert_error(response, 422, "validation_error")
    assert [issue["loc"] for issue in body["detail"]] == [["body", "name"]]


def test_other_users_note_is_not_found(
    auth_client: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    note = create_note(register_user().client)

    response = auth_client.get(f"/notes/{note['id']}")

    assert_error(response, 404, "not_found", f"Note {note['id']} not found")


def test_requires_a_session(api: httpx.Client) -> None:
    assert_error(api.get("/notes"), 403, "http_error", "Not authenticated")
```

Style:
- Plain sync test functions. Arrange through the API, act with one request,
  assert on the response **and** on a follow-up GET.
- `from __future__ import annotations`; type-only imports under
  `TYPE_CHECKING` (ruff strict type-checking).
- Never import `app` in tests: the app runs in another process.
- Use `unique_email()` for emails (real TLD `@example.com`; the backend
  rejects reserved TLDs like `.test`).

### Backend guards

| Guard | When | Fails when | Fix |
|---|---|---|---|
| 1. End-to-end only | collection, before Docker starts (+ ruff `TID251`) | a test file outside `tests/e2e/`; `import app` under `tests/`; a banned fixture (`monkeypatch`, `mocker`, `httpx_mock`, `respx_mock`, `requests_mock`, `freezer`, `time_machine`, `httpserver`, `vcr`, `fs`, ...); a banned construct in `tests/**` or any backend `conftest.py` (`unittest.mock`, `Mock`, `patch`, `monkeypatch`, `setattr(`, `sys.modules`, `dependency_overrides`, `TestClient`, `ASGITransport`, `MockTransport`, `transport=`, `sqlite`, `.create_all(`, ...) | Use the live-server fixtures. Only `tests/e2e/guards.py` may name these. |
| 2. Route coverage | end of a **full** run | an app route (HEAD ignored) has no response < 400. Message: `never requested` or `only error responses (codes)` | Add a test that calls the route successfully. |
| 3. `alembic check` | session start | models and migrations differ | `uv run alembic revision --autogenerate -m "..."`, review, commit. |

- Guard 2 is skipped for partial runs (a path or node id, `-k`, `-m`, `--lf`,
  `-x` stop, `--collect-only`) and when the stack never started.
- `ROUTE_COVERAGE_ALLOWLIST` in `tests/e2e/guards.py` (empty today) is only for
  a route that cannot succeed without a third party; every entry needs a reason.
  `KNOWN_GAPS` lists covered routes with a path no test can reach; each full run
  prints it.
- `.pre-commit-config.yaml` has a faster grep guard (`no-mocks-backend-tests`).

### Run one backend test

```bash
cd backend
uv run pytest tests/e2e/test_items.py -v
uv run pytest tests/e2e/test_items.py::test_create_without_description_stores_null -v
uv run pytest -k "login"
```

On failure, pytest prints "Captured server output" (the server's log lines for
that test).

---

## Frontend (full-stack) suite

### How the stack starts

`cd frontend && bun run test:e2e` (same as `bun run test`). Playwright starts
three `webServer` entries through `e2e/support/stack.sh`, in order:

| Piece | Address | Details |
|---|---|---|
| db | 127.0.0.1:55432 | container `e2e-postgres-<port>`, tmpfs, image of the compose `db` service |
| backend | 127.0.0.1:59095 | `uv run alembic upgrade head`, then uvicorn with explicit env (`DB_URL`, `FRONTEND_URL`, `LOG_LEVEL=ERROR`) |
| frontend | 127.0.0.1:53000 | `vite dev` with `VITE_API_BASE_URL` = the e2e backend |

The dev ports (5432, 9095, 3000) are never touched. Each piece stops if the
Playwright runner dies.

The TanStack devtools event bus always listens on port 42069.
`vite.config.ts` turns it off when `E2E_RUNNER_PID` is set (Playwright sets
it), so the e2e frontend shares no port with `bun run dev` or another e2e run.

One-time setup: `bun install`, `cd ../backend && uv sync`,
`bunx playwright install --with-deps chromium`. Linux, macOS and CI only (bash).

Env overrides: `E2E_DB_PORT`, `E2E_BACKEND_PORT`, `E2E_FRONTEND_PORT` (set
them to run two checkouts at once), `E2E_DB_IMAGE`. `E2E_REUSE=1` reuses a
stack that is already running (never in CI); without it a busy e2e port fails
the run.

Config (`playwright.config.ts`): only `*.spec.ts` run, `forbidOnly: true`,
`retries: 0` (fix a flaky test, do not retry it; ESLint rejects a `retries` override in specs), traces and screenshots kept
on failure.

### Fixtures (`e2e/fixtures.ts`)

Every spec starts with:

```ts
import { test, expect } from './fixtures'
```

| Fixture | What |
|---|---|
| `page` | Playwright page (anonymous) |
| `api` | `APIRequestContext` with `baseURL` = the real backend, no auth header |
| `user` | a new user registered through `POST /auth/register` (`email`, `password`, `token`) |
| `authedPage` | a page in its own context, signed in as `user` |
| `loginAs(user)` | a new signed-in page for any other user |

Helpers:

| Helper | Signature / value |
|---|---|
| `registerUser` | `registerUser(api, email = uniqueEmail(), password = PASSWORD): Promise<TestUser>` (sends `{ email, raw_password }` to `POST /auth/register`) |
| `loginUser` | `loginUser(api, email, password): Promise<string>` (the new session token) |
| `createItem` | `createItem(api, owner, data): Promise<Item>` |
| `createItems` | `createItems(api, owner, names): Promise<Item[]>` (in order) |
| `listItems` | `listItems(api, owner): Promise<Item[]>` |
| `authHeaders` | `authHeaders(user)` -> `{ Authorization: 'Bearer <token>' }` |
| `uniqueEmail` | `uniqueEmail(label = 'user')` -> `e2e-<label>-<uuid>@example.com` |
| `PASSWORD` | a password that meets the register rules |
| `errorToast(page)`, `storedToken(page)` | error toast locator; the stored session token or `null` |
| `BACKEND_URL`, `FRONTEND_URL` | the e2e stack URLs |

`TestUser` is `{ email, password, token }`.
Every context also fails the test on an uncaught app error.

### Worked example: `e2e/notes.spec.ts`

First add seed helpers to `e2e/fixtures.ts`, next to `createItem` (they call the
real API; this is also how the endpoint guard sees `/notes`). The guard also
needs every `DETAIL` entry: for ``(id) => `/notes/${id}` ``, a
`` `/notes/${...}` `` string must appear in a spec or in `fixtures.ts`. The delete test
below does this with a direct `api.get`, as `items.spec.ts` does:

```ts
export async function createNote(
  api: APIRequestContext,
  owner: TestUser,
  data: CreateNoteData
): Promise<Note> {
  const response = await api.post('/notes', { data, headers: authHeaders(owner) })
  await expectOk(response, 'POST /notes')
  return (await response.json()) as Note
}

export async function listNotes(api: APIRequestContext, owner: TestUser): Promise<Note[]> {
  const response = await api.get('/notes?size=100', { headers: authHeaders(owner) })
  await expectOk(response, 'GET /notes')
  return ((await response.json()) as NotesResponse).items
}
```

Then the spec:

```ts
import { test, expect, authHeaders, createNote, listNotes, registerUser } from './fixtures'

test('creates a note through the dialog', async ({ authedPage: page, api, user }) => {
  await page.goto('/notes')
  await page.getByRole('button', { name: 'Create Note' }).click()
  const dialog = page.getByRole('dialog', { name: 'Create New Note' })
  await dialog.getByLabel('Name').fill('Groceries')
  await dialog.getByRole('button', { name: 'Create', exact: true }).click()

  await expect(dialog).toBeHidden()
  await expect(page.getByText('Groceries')).toBeVisible()
  expect((await listNotes(api, user)).map(n => n.name)).toEqual(['Groceries'])
})

test('deletes a note', async ({ authedPage: page, api, user }) => {
  const note = await createNote(api, user, { name: 'Old' })
  await page.goto('/notes')
  await page.getByRole('button', { name: 'Delete Old' }).click()
  const confirm = page.getByRole('alertdialog')
  await confirm.getByRole('button', { name: 'Delete' }).click()

  // Wait for the dialog first: its text (delete "Old"?) also contains 'Old'.
  await expect(confirm).toBeHidden()
  await expect(page.getByText('Old', { exact: true })).toBeHidden()
  expect(await listNotes(api, user)).toEqual([])
  const gone = await api.get(`/notes/${note.id}`, { headers: authHeaders(user) })
  expect(gone.status()).toBe(404) // also covers API.NOTES.DETAIL for the guard
})

test('shows only my own notes', async ({ authedPage: page, api, user }) => {
  const other = await registerUser(api) // a second user
  await createNote(api, other, { name: 'Not mine' })
  await createNote(api, user, { name: 'Mine' })
  await page.goto('/notes')
  await expect(page.getByText('Mine', { exact: true })).toBeVisible() // list loaded
  await expect(page.getByText('Not mine')).toBeHidden()
})

test('sends anonymous users to login', async ({ page }) => {
  await page.goto('/notes')
  await expect(page).toHaveURL('/login?redirect=%2Fnotes')
})
```

Style:
- Find elements by role, label and text (`getByRole`, `getByLabel`); add a
  `data-testid` only when nothing else is unique (see `item-card`).
- Never sleep. `expect(...)` retries until the UI matches.
- Check the result twice: in the UI and through the `api` fixture.

### Frontend guards

**ESLint** (`bun run lint`, on all `e2e/**` JS/TS files):
- `page`/`context` `.route`, `routeFromHAR`, `unroute`, `unrouteAll`,
  `routeWebSocket`, `fulfill`, `addInitScript`, `addScriptTag`, `setContent`, `newCDPSession`,
  `newBrowserCDPSession`, `waitForTimeout`.
  The same network bans apply in `src/`. Specs may import from `src/` only
  `lib/api-endpoints`, `lib/auth` and `types/*`.
- Assigning or defining `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`,
  `Response`, `Request`, `Headers`, or patching their `prototype`; using one of
  those names or a route method name as a string to reach it (`window['fetch']`,
  `Reflect.set(…, 'fetch')`, `const r = 'route'`). Plain strings such as
  `resourceType() === 'fetch'` are fine.
- CDP network commands as strings (`'Fetch.enable'`, `'Fetch.fulfillRequest'`, `'Network.…'`).
- Setting `retries` in a spec (`test.describe.configure({ retries })`);
  `retries: 0` in `playwright.config.ts` is the rule.
- A string of code passed to `evaluate`, `evaluateHandle`, `evaluateAll`,
  `$eval`, `$$eval` (pass a function).
- Importing `@playwright/test`, `playwright`, `playwright-core` (or subpaths)
  outside `fixtures.ts`; dynamic `import()` and `require()`.
- `.skip`, `.fixme`, `.only`, `.fail` (only with an `eslint-disable` comment
  that gives a reason).
- In the whole frontend: importing `msw`, `nock`, `sinon`, `fetch-mock`,
  `miragejs`, `json-server`, `vitest`, `jest`, `@testing-library/*`, `jsdom`,
  `happy-dom`, ...

**`e2e/guards.spec.ts`** (runs with the suite; comments do not count):
- every test file in `e2e/` is a `*.spec.ts` (Playwright runs nothing else);
  helpers go in `e2e/support/`.
- every page route in `src/routeTree.gen.ts` is opened by a spec with
  `page.goto('/path')` or `toHaveURL('/path')`;
- every endpoint in `src/lib/api-endpoints.ts` appears as a string in a spec
  or in `e2e/fixtures.ts`;
- no mock or unit-test library is in `package.json`, and no
  `public/mockServiceWorker.js`.

`.pre-commit-config.yaml` also has a grep guard (`no-mocks-frontend-e2e`).

### Run one spec and debug

```bash
cd frontend
bun run test:e2e e2e/items.spec.ts
bun run test:e2e -g "creates an item"
bunx playwright show-trace test-results/<test-folder>/trace.zip
```

Server output is prefixed `[db]`, `[backend]` (errors only) and `[frontend]`.

---

## Third-party services

Never fake a third party (no mock server, no recorded responses, no patched
client). Instead:

1. Test every path that does not need the provider: input validation, the
   "provider is down" path (the backend suite points provider URLs at a closed
   local port), error redirects, "not configured" behaviour.
2. Seed the state the provider would create through the API, or with `db`
   when no endpoint can (see `create_passwordless_user` in
   `tests/e2e/helpers.py`).
3. If a route cannot succeed at all without the provider, add it to
   `ROUTE_COVERAGE_ALLOWLIST` with the reason. If the route is covered but one
   path is not, add it to `KNOWN_GAPS`. Example: Google sign-in
   (`tests/e2e/test_oauth.py`, `e2e/oauth.spec.ts`).

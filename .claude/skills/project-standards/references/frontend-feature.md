# Add a frontend feature

Recipe for a new feature in `frontend/src/`. Every snippet is the real
`items` feature with the names changed to a `notes` example. When in doubt,
open the items file and copy it:

| Piece | Items reference |
|---|---|
| Types | `src/types/item.ts` |
| Endpoints + URL builder | `src/lib/api-endpoints.ts` |
| Query keys | `src/lib/query-keys.ts` |
| Zod schema | `src/features/items/item-schemas.ts` |
| Query + mutation hooks | `src/hooks/useItems.ts` |
| Dialogs | `src/components/ItemFormDialog.tsx`, `CreateItemDialog.tsx`, `EditItemDialog.tsx`, `DeleteItemDialog.tsx` |
| Page | `src/routes/_authed/items.tsx` |
| E2E | `e2e/items.spec.ts`, helpers in `e2e/fixtures.ts` |

Stack: React 19, TanStack Start + Router (file routes), TanStack Query,
react-hook-form + Zod, Tailwind v4, shadcn/ui, bun. Run commands from `frontend/`.

**Read-only page (list only)?** Steps 4 and 6 are optional, and you need only
the query hook. Add to `API` only the endpoints the UI calls: every entry
must be used by a spec or `e2e/fixtures.ts`, or `e2e/guards.spec.ts` fails.

## Layout

```
src/
├── types/note.ts                      # API shapes
├── lib/api-endpoints.ts               # + API.NOTES, buildNotesListUrl
├── lib/query-keys.ts                  # + queryKeys.notes
├── features/notes/note-schemas.ts     # Zod form schema + form -> payload
├── hooks/useNotes.ts                  # useNotes, useCreateNote, useUpdateNote, useDeleteNote
├── components/NoteFormDialog.tsx      # + CreateNoteDialog, EditNoteDialog, DeleteNoteDialog
└── routes/_authed/notes.tsx           # the /notes page (signed-in users)
```

Rules: components stay flat in `src/components/` (no feature subfolders);
`src/components/ui/` is shadcn only; `src/lib/` is generic infrastructure plus
the endpoint list; hooks are flat in `src/hooks/`.

## 1. Types (`src/types/note.ts`)

Match the backend response exactly (field names are snake_case, dates are ISO
strings). Copy the fields from the backend `<Entity>Response` schema.

```ts
export interface NotesParams {
  page?: number
  size?: number
  /** Sent to the API as `name__ilike` for case-insensitive substring match */
  name?: string
}

export interface Note {
  id: string
  user_id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface NotesResponse {
  items: Note[]
  total: number
  page?: number
  size?: number
  pages?: number
}

export interface CreateNoteData {
  name: string
  description?: string | null
}

export interface UpdateNoteData {
  name?: string
  /** `null` clears the description; a missing key leaves it unchanged. */
  description?: string | null
}
```

## 2. Endpoints (`src/lib/api-endpoints.ts`)

Paths have no `/api` prefix: the backend serves `/items`, `/auth/...` at the root.

```ts
export const API = {
  // ... AUTH, ITEMS ...
  NOTES: {
    LIST: '/notes',
    CREATE: '/notes',
    DETAIL: (id: string) => `/notes/${id}`, // GET, PATCH, DELETE
  },
} as const

/** Translates semantic params to wire keys (name -> name__ilike=%name%). */
export function buildNotesListUrl(params?: NotesParams): string {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', params.page.toString())
  if (params?.size) queryParams.append('size', params.size.toString())
  if (params?.name) queryParams.append('name__ilike', `%${escapeLikePattern(params.name)}%`)
  const queryString = queryParams.toString()
  return queryString ? `${API.NOTES.LIST}?${queryString}` : API.NOTES.LIST
}
```

`escapeLikePattern` is already in the file (makes `%`, `_`, `\` literal).
Every endpoint here must be used by an e2e spec or `e2e/fixtures.ts`, or
`e2e/guards.spec.ts` fails.

## 3. Query keys (`src/lib/query-keys.ts`)

```ts
export const queryKeys = {
  // ... items ...
  notes: {
    all: ['notes'] as const,
    list: (params?: NotesParams) => ['notes', 'list', params] as const,
  },
}
```

First level = feature; always include the params in the key.

## 4. Form schema (`src/features/notes/note-schemas.ts`)

Mirror the backend limits, so the user sees the error before the request:

```ts
import { z } from 'zod'

export const noteSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255, 'Name must be less than 255 characters'),
  description: z.string().max(5000, 'Description must be less than 5000 characters').optional(),
})

export type NoteFormData = z.infer<typeof noteSchema>

/**
 * Maps form values to the mutation payload shape.
 * An empty description is sent as `null`, not left out: the update endpoint
 * keeps fields that are missing from the body, so `null` is how a user clears it.
 */
export function noteFormToPayload(data: NoteFormData) {
  return { name: data.name, description: data.description || null }
}
```

## 5. Hooks (`src/hooks/useNotes.ts`)

```ts
import { keepPreviousData, useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API, buildNotesListUrl } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import type { Note, NotesParams, NotesResponse, CreateNoteData, UpdateNoteData } from '@/types/note'

export function useNotes(params?: NotesParams, enabled = true) {
  return useQuery({
    queryKey: queryKeys.notes.list(params),
    queryFn: () => api.get<NotesResponse>(buildNotesListUrl(params)),
    enabled,
    // Keep the current page on screen while the next page or search loads.
    placeholderData: keepPreviousData,
  })
}

export function useCreateNote() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateNoteData) => api.post<Note>(API.NOTES.CREATE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all })
    },
  })
}

export function useUpdateNote(noteId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UpdateNoteData) => api.patch<Note>(API.NOTES.DETAIL(noteId), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all })
    },
  })
}

export function useDeleteNote(noteId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.delete(API.NOTES.DETAIL(noteId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notes.all })
    },
  })
}
```

`useDeleteItem` in `useItems.ts` shows an optimistic delete with rollback
(`onMutate` / `onError` / `onSettled`); copy it when the UI must update at once.

`api` (`src/lib/api-client.ts`) has `get`, `post`, `put`, `patch`, `delete`.
It adds `Authorization: Bearer <token>` and throws `ApiError` on any non-2xx.

## 6. Components

Copy the items dialogs and rename:
- `NoteFormDialog.tsx`: shadcn `Dialog` + `Form` + `FormField`/`FormLabel`/
  `FormControl`/`FormMessage`, `useForm({ resolver: zodResolver(noteSchema) })`.
  On submit: `await onSubmit(data)`, close; on error
  `toastApiError(error, 'Failed to create note')`.
- `CreateNoteDialog.tsx` / `EditNoteDialog.tsx`: wire the mutation hook to the
  form dialog (`await createNote.mutateAsync(noteFormToPayload(data))`).
- `DeleteNoteDialog.tsx`: shadcn `AlertDialog`; `AlertDialogAction` takes
  `variant="destructive"`.

Rules:
- `FormControl` puts the id and aria attributes on its only child, so
  `<FormLabel>` names the input. Tests find fields with `getByLabel`.
- Icon-only buttons need `aria-label` (jsx-a11y is on).
- `Button` has no `asChild`. To style a `Link` as a button use
  `className={buttonVariants({ variant: 'outline' })}`.
- Errors: `toastApiError(error, title)` shows one toast (title + reason).
  `getErrorMessage(error)` gives the text for inline error states.

## 7. Page (`src/routes/_authed/notes.tsx`)

```tsx
import { createFileRoute } from '@tanstack/react-router'
import { useNotes } from '@/hooks/useNotes'

// Signed-in users only: the _authed layout guards every page in routes/_authed/.
export const Route = createFileRoute('/_authed/notes')({
  component: Notes,
})

function Notes() {
  const { data, isLoading, isError, error } = useNotes({ page: 1, size: 9 })
  // loading state, error state (getErrorMessage), empty state, list - see items.tsx
}
```

- Pages for signed-in users go in `src/routes/_authed/`. The folder name is
  not in the URL. The `_authed` layout is client-only (`ssr: false`) and sends
  anonymous users to `/login?redirect=<page>`.
- Never redirect in `beforeLoad`: the token is in localStorage (the server
  cannot read it), and a redirect during hydration breaks the page.
- Public pages go directly in `src/routes/`. A server-rendered form there must
  stay disabled until `useHydrated()` (`src/hooks/useHydrated.ts`) is true,
  like `src/routes/login.tsx`. Use `noValidate` so the Zod messages show.
- `src/routeTree.gen.ts` is regenerated by `bun run dev` or `bun run build`.
  Do not edit it by hand; commit the regenerated file.
- After you add or rename a route file, run `bun run build` once (or keep
  `bun run dev` running) **before** `bun run typecheck`. (`make check` builds
  first, so it is safe.) A stale `routeTree.gen.ts` fails `tsc` with `"/notes" is not assignable ...` /
  `"/_authed/notes" is not keyof FileRoutesByPath`.

## 8. Navigation (`src/components/Navigation.tsx`)

Add a `Link` next to Items, inside `{isAuthenticated && (...)}` for protected pages:

```tsx
<Link to="/notes" className="..." activeProps={{ className: 'text-foreground after:w-full' }}>
  Notes
</Link>
```

## 9. Errors from the API

| Case | What the app gets |
|---|---|
| Any backend error | `ApiError` with `status`, `message` (= backend `detail`), `code` (= backend `error_code`) |
| 422 | `fields` = `{ <field>: [msg, ...] }`, message `"field: msg; ..."` |
| 401 with a token, or 403 `Not authenticated` | token cleared, message `Your session has expired. Please sign in again.`; `_authed` pages go to `/login?redirect=...` |
| 401 without a token (wrong password) | the backend `detail` |
| Network failure | `status` 0, `code` `network_error` |

## 10. E2E tests (mandatory)

1. In `e2e/fixtures.ts`, next to `createItem`, add seed helpers that call the
   real API (`createNote(api, owner, data)`, `listNotes(api, owner)`).
2. Write `e2e/notes.spec.ts` that imports `{ test, expect } from './fixtures'`:
   open the page with `page.goto('/notes')`, drive the UI, check the result in
   the UI and through the `api` fixture.
3. Cover: empty state, create, validation message, edit, clearing an optional
   field (save an empty description, then check it is `null` through the API),
   delete, search and pages (if any), and the anonymous redirect to
   `/login?redirect=...`.

The guards fail if `/notes` is never visited or an endpoint in `API.NOTES` is
never used. See [e2e-testing.md](e2e-testing.md).

## Checklist

- [ ] `types/<feature>.ts` matches the backend response
- [ ] `API.<FEATURE>` (+ list URL builder) in `lib/api-endpoints.ts`
- [ ] `queryKeys.<feature>` in `lib/query-keys.ts`
- [ ] Zod schema in `features/<feature>/<entity>-schemas.ts` (e.g. `features/notes/note-schemas.ts`)
- [ ] hooks in `hooks/use<Feature>.ts`; mutations invalidate `queryKeys.<feature>.all`
- [ ] dialogs in `components/`, errors via `toastApiError`
- [ ] page in `routes/_authed/` (or `routes/` if public, with `useHydrated`)
- [ ] nav link
- [ ] `e2e/<feature>.spec.ts` + helpers in `e2e/fixtures.ts`
- [ ] `bun run lint`, `bun run format:check`, `bun run build` (regenerates `routeTree.gen.ts`), `bun run typecheck`, `bun run test:e2e` green

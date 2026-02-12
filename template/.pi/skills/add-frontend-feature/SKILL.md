---
name: add-frontend-feature
description: Step-by-step guide to add a new feature to the React frontend. Covers TypeScript types, API endpoints, query hooks, mutation hooks, components, routes, and dialogs. Use when creating new UI features connected to backend APIs.
---

# Add Frontend Feature

Sequential guide for adding a new feature module to the React frontend. The `items` feature is the canonical reference.

## Step 1: Types (`types/your-entity.ts`)

```typescript
export interface YourEntity {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface YourEntityCreate {
  name: string
  description?: string
}

export interface YourEntityUpdate {
  name?: string
  description?: string
}
```

## Step 2: API Endpoints (`lib/api-endpoints.ts`)

Add to the `API` constant:

```typescript
export const API = {
  // ... existing endpoints ...
  YOUR_ENTITIES: {
    LIST: '/api/v1/your-entities',
    CREATE: '/api/v1/your-entities',
    DETAIL: (id: string) => `/api/v1/your-entities/${id}`,
    UPDATE: (id: string) => `/api/v1/your-entities/${id}`,
    DELETE: (id: string) => `/api/v1/your-entities/${id}`,
  },
} as const
```

## Step 3: Query Keys (`lib/query-keys.ts`)

Add a key factory:

```typescript
export const queryKeys = {
  // ... existing keys ...
  yourEntities: {
    all: ['your-entities'] as const,
    list: () => [...queryKeys.yourEntities.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.yourEntities.all, 'detail', id] as const,
  },
}
```

## Step 4: Zod Schema (`lib/schemas/your-entity.ts`)

```typescript
import { z } from 'zod'

export const yourEntitySchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().max(5000).optional(),
})

export type YourEntityFormData = z.infer<typeof yourEntitySchema>
```

## Step 5: Query Hook (`hooks/queries/useYourEntitiesQuery.ts`)

```typescript
import { queryOptions } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import type { YourEntity } from '@/types/your-entity'

export const yourEntitiesQueryOptions = () =>
  queryOptions({
    queryKey: queryKeys.yourEntities.list(),
    queryFn: () => api.get<YourEntity[]>(API.YOUR_ENTITIES.LIST),
    staleTime: 1000 * 60 * 5,
  })

export const yourEntityDetailQueryOptions = (id: string) =>
  queryOptions({
    queryKey: queryKeys.yourEntities.detail(id),
    queryFn: () => api.get<YourEntity>(API.YOUR_ENTITIES.DETAIL(id)),
    staleTime: 1000 * 60 * 5,
  })
```

## Step 6: Mutation Hooks (`hooks/mutations/useYourEntityMutations.ts`)

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import { API } from '@/lib/api-endpoints'
import { queryKeys } from '@/lib/query-keys'
import type { YourEntityCreate, YourEntityUpdate } from '@/types/your-entity'

export function useCreateYourEntity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: YourEntityCreate) =>
      api.post(API.YOUR_ENTITIES.CREATE, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.yourEntities.all })
    },
  })
}

export function useUpdateYourEntity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: YourEntityUpdate }) =>
      api.patch(API.YOUR_ENTITIES.UPDATE(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.yourEntities.all })
    },
  })
}

export function useDeleteYourEntity() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(API.YOUR_ENTITIES.DELETE(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.yourEntities.all })
    },
  })
}
```

## Step 7: Components

### List Component (`components/your-entities/YourEntitiesList.tsx`)

```typescript
import { useQuery } from '@tanstack/react-query'
import { yourEntitiesQueryOptions } from '@/hooks/queries/useYourEntitiesQuery'

export function YourEntitiesList() {
  const { data, isLoading, error } = useQuery(yourEntitiesQueryOptions())

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return (
    <div>
      {data?.map((entity) => (
        <div key={entity.id}>{entity.name}</div>
      ))}
    </div>
  )
}
```

### Form Dialog (`components/your-entities/dialogs/YourEntityFormDialog.tsx`)

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { yourEntitySchema, type YourEntityFormData } from '@/lib/schemas/your-entity'
import { useCreateYourEntity } from '@/hooks/mutations/useYourEntityMutations'
import { toast } from 'sonner'

export function CreateYourEntityDialog() {
  const createMutation = useCreateYourEntity()
  const form = useForm<YourEntityFormData>({
    resolver: zodResolver(yourEntitySchema),
    defaultValues: { name: '', description: '' },
  })

  async function onSubmit(data: YourEntityFormData) {
    try {
      await createMutation.mutateAsync(data)
      toast.success('Created successfully')
    } catch (error) {
      toast.error('Failed to create')
    }
  }

  return (
    // Use shadcn/ui Dialog + Form components
    // See components/ui/ for available primitives
  )
}
```

## Step 8: Route (`routes/your-entities.tsx`)

```typescript
import { createFileRoute } from '@tanstack/react-router'
import { YourEntitiesList } from '@/components/your-entities/YourEntitiesList'

export const Route = createFileRoute('/your-entities')({
  component: YourEntitiesPage,
})

function YourEntitiesPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">Your Entities</h1>
      <YourEntitiesList />
    </div>
  )
}
```

After creating the route file, run `bun run dev` to auto-generate the route tree.

## Step 9: Navigation

Add a link in `components/common/Navigation.tsx`:

```typescript
<Link to="/your-entities">Your Entities</Link>
```

## Folder Structure Result

```
src/
├── types/your-entity.ts
├── lib/
│   ├── api-endpoints.ts        (updated)
│   ├── query-keys.ts           (updated)
│   └── schemas/your-entity.ts
├── hooks/
│   ├── queries/useYourEntitiesQuery.ts
│   └── mutations/useYourEntityMutations.ts
├── components/
│   └── your-entities/
│       ├── YourEntitiesList.tsx
│       └── dialogs/
│           └── YourEntityFormDialog.tsx
└── routes/
    └── your-entities.tsx
```

## Checklist

- [ ] Types defined in `types/`
- [ ] API endpoints added to `api-endpoints.ts`
- [ ] Query keys added to `query-keys.ts`
- [ ] Zod schema in `lib/schemas/`
- [ ] Query hook(s) in `hooks/queries/`
- [ ] Mutation hook(s) in `hooks/mutations/`
- [ ] List/detail components in `components/{feature}/`
- [ ] Form dialog with Zod + react-hook-form
- [ ] Route file in `routes/`
- [ ] Navigation link added
- [ ] Error handling with toast notifications
- [ ] Tests written

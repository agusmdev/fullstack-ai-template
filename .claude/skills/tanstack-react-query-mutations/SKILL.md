---
name: tanstack-react-query-mutations
description: Mutation patterns with useMutation, optimistic updates, cache invalidation, and rollback strategies. SHARED skill for both TanStack Start (SSR) and TanStack Router (SPA).
---

# TanStack Query Mutations

## Overview

This skill covers mutation patterns for creating, updating, and deleting data using TanStack Query's `useMutation` hook. Includes optimistic updates, cache invalidation, error handling, and rollback strategies.

**Important:** This skill works for both:
- TanStack Start (SSR full-stack)
- TanStack Router (SPA client-only)

## Prerequisites

- TanStack Query installed and configured (see `tanstack-react-query-setup` skill)
- Query patterns understanding (see `tanstack-react-query-patterns` skill)
- API layer set up (see `tanstack-client-api-layer` skill)

## Pattern 1: Basic Mutation

Simple mutation without cache updates:

### Create Mutation Definition

```typescript
// src/mutations/user.mutations.ts
import { useMutation } from '@tanstack/react-query'
import { createUser, updateUser, deleteUser } from '~/api/users'

export function useCreateUser() {
  return useMutation({
    mutationFn: createUser,
    onSuccess: (data) => {
      console.log('User created:', data)
    },
    onError: (error) => {
      console.error('Failed to create user:', error)
    },
  })
}

export function useUpdateUser() {
  return useMutation({
    mutationFn: updateUser,
  })
}

export function useDeleteUser() {
  return useMutation({
    mutationFn: deleteUser,
  })
}
```

### Usage in Component

```tsx
import { useCreateUser } from '~/mutations/user.mutations'
import { toast } from '~/components/ui/use-toast'

export function CreateUserForm() {
  const createUser = useCreateUser()

  const handleSubmit = async (data: UserInput) => {
    try {
      const newUser = await createUser.mutateAsync(data)
      toast({ title: 'User created!', description: newUser.name })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message,
      })
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button disabled={createUser.isPending}>
        {createUser.isPending ? 'Creating...' : 'Create User'}
      </button>
    </form>
  )
}
```

## Pattern 2: Mutation with Cache Invalidation

Automatically refetch related queries after mutation:

### Invalidate Specific Queries

```typescript
// src/mutations/post.mutations.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createPost, updatePost, deletePost } from '~/api/posts'
import { queryKeys } from '~/lib/query-keys'

export function useCreatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createPost,
    onSuccess: () => {
      // Invalidate all post list queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.posts.lists(),
      })
    },
  })
}

export function useUpdatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updatePost,
    onSuccess: (updatedPost) => {
      // Invalidate specific post detail
      queryClient.invalidateQueries({
        queryKey: queryKeys.posts.detail(updatedPost.id),
      })
      // Also invalidate lists (post might appear in filtered lists)
      queryClient.invalidateQueries({
        queryKey: queryKeys.posts.lists(),
      })
    },
  })
}

export function useDeletePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deletePost,
    onSuccess: (_, deletedPostId) => {
      // Remove from cache
      queryClient.removeQueries({
        queryKey: queryKeys.posts.detail(deletedPostId),
      })
      // Invalidate lists
      queryClient.invalidateQueries({
        queryKey: queryKeys.posts.lists(),
      })
    },
  })
}
```

### Invalidate Multiple Related Queries

```typescript
export function useUpdateUserProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateUserProfile,
    onSuccess: (updatedUser) => {
      // Invalidate user-related queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.detail(updatedUser.id),
      })
      queryClient.invalidateQueries({
        queryKey: queryKeys.users.lists(),
      })
      // Also invalidate posts by this user
      queryClient.invalidateQueries({
        queryKey: queryKeys.posts.lists(),
      })
    },
  })
}
```

## Pattern 3: Optimistic Updates

Update UI immediately before server confirms:

### Basic Optimistic Update

```typescript
// src/mutations/post.mutations.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updatePost } from '~/api/posts'
import { queryKeys } from '~/lib/query-keys'
import type { Post } from '~/types'

export function useUpdatePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updatePost,
    onMutate: async (updatedPost) => {
      // Cancel outgoing refetches (so they don't overwrite optimistic update)
      await queryClient.cancelQueries({
        queryKey: queryKeys.posts.detail(updatedPost.id),
      })

      // Snapshot previous value
      const previousPost = queryClient.getQueryData<Post>(
        queryKeys.posts.detail(updatedPost.id)
      )

      // Optimistically update to new value
      queryClient.setQueryData<Post>(
        queryKeys.posts.detail(updatedPost.id),
        updatedPost
      )

      // Return context with snapshot
      return { previousPost }
    },
    onError: (err, updatedPost, context) => {
      // Rollback to previous value on error
      if (context?.previousPost) {
        queryClient.setQueryData<Post>(
          queryKeys.posts.detail(updatedPost.id),
          context.previousPost
        )
      }
    },
    onSettled: (updatedPost) => {
      // Refetch to ensure sync with server
      if (updatedPost) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.posts.detail(updatedPost.id),
        })
      }
    },
  })
}
```

### Optimistic Update with List

```typescript
export function useDeletePost() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deletePost,
    onMutate: async (postId) => {
      // Cancel refetches
      await queryClient.cancelQueries({
        queryKey: queryKeys.posts.lists(),
      })

      // Snapshot all list queries
      const previousLists = queryClient.getQueriesData<Post[]>({
        queryKey: queryKeys.posts.lists(),
      })

      // Optimistically remove from all lists
      queryClient.setQueriesData<Post[]>(
        { queryKey: queryKeys.posts.lists() },
        (old) => old?.filter((post) => post.id !== postId)
      )

      return { previousLists }
    },
    onError: (err, postId, context) => {
      // Restore all list queries
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data)
        })
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.posts.lists(),
      })
    },
  })
}
```

## Pattern 4: Sequential Mutations

Chain multiple mutations together:

### Using mutateAsync

```tsx
import { useCreatePost } from '~/mutations/post.mutations'
import { useUploadImage } from '~/mutations/media.mutations'
import { toast } from '~/components/ui/use-toast'

export function CreatePostForm() {
  const uploadImage = useUploadImage()
  const createPost = useCreatePost()

  const handleSubmit = async (data: PostInput) => {
    try {
      // First upload image
      const uploadedImage = await uploadImage.mutateAsync(data.imageFile)

      // Then create post with image URL
      const newPost = await createPost.mutateAsync({
        ...data,
        imageUrl: uploadedImage.url,
      })

      toast({ title: 'Post created!', description: newPost.title })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message,
      })
    }
  }

  const isLoading = uploadImage.isPending || createPost.isPending

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button disabled={isLoading}>
        {isLoading ? 'Creating...' : 'Create Post'}
      </button>
    </form>
  )
}
```

### Custom Hook for Sequential Mutations

```typescript
// src/hooks/use-create-post-with-image.ts
import { useMutation } from '@tanstack/react-query'
import { uploadImage } from '~/api/media'
import { createPost } from '~/api/posts'

export function useCreatePostWithImage() {
  return useMutation({
    mutationFn: async (data: PostInput) => {
      // Upload image first
      const uploadedImage = await uploadImage(data.imageFile)

      // Then create post
      return createPost({
        ...data,
        imageUrl: uploadedImage.url,
      })
    },
  })
}
```

## Pattern 5: Parallel Mutations

Execute multiple mutations simultaneously:

```tsx
import { useUpdateUser } from '~/mutations/user.mutations'
import { useUpdatePreferences } from '~/mutations/preferences.mutations'

export function UpdateProfileForm() {
  const updateUser = useUpdateUser()
  const updatePreferences = useUpdatePreferences()

  const handleSubmit = async (data: ProfileInput) => {
    try {
      // Run mutations in parallel
      await Promise.all([
        updateUser.mutateAsync(data.user),
        updatePreferences.mutateAsync(data.preferences),
      ])

      toast({ title: 'Profile updated!' })
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error updating profile',
      })
    }
  }

  const isLoading = updateUser.isPending || updatePreferences.isPending

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save'}
      </button>
    </form>
  )
}
```

## Pattern 6: Global Mutation Defaults

Set default behavior for all mutations:

```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'
import { toast } from '~/components/ui/use-toast'

export const queryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      onError: (error) => {
        // Global error handling
        toast({
          variant: 'destructive',
          title: 'Error',
          description: error.message,
        })
      },
      onSuccess: () => {
        // Global success handling (optional)
        console.log('Mutation succeeded')
      },
      retry: 1, // Retry failed mutations once
      retryDelay: 1000, // Wait 1 second before retry
    },
  },
})
```

## Pattern 7: Mutation with Form Libraries

Integrate with React Hook Form:

### Basic Integration

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreatePost } from '~/mutations/post.mutations'
import { Form, FormField, FormItem, FormLabel, FormControl } from '~/components/ui/form'
import { Input } from '~/components/ui/input'
import { Button } from '~/components/ui/button'

const postSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  content: z.string().min(10, 'Content must be at least 10 characters'),
})

type PostFormData = z.infer<typeof postSchema>

export function CreatePostForm() {
  const createPost = useCreatePost()
  const form = useForm<PostFormData>({
    resolver: zodResolver(postSchema),
    defaultValues: {
      title: '',
      content: '',
    },
  })

  const onSubmit = async (data: PostFormData) => {
    await createPost.mutateAsync(data)
    form.reset()
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="content"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Content</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <Button type="submit" disabled={createPost.isPending}>
          {createPost.isPending ? 'Creating...' : 'Create Post'}
        </Button>
      </form>
    </Form>
  )
}
```

## Pattern 8: Mutation State Management

Track and display mutation state:

### Loading States

```tsx
import { useCreatePost } from '~/mutations/post.mutations'
import { Loader2 } from 'lucide-react'

export function CreatePostButton({ data }: { data: PostInput }) {
  const createPost = useCreatePost()

  return (
    <button
      onClick={() => createPost.mutate(data)}
      disabled={createPost.isPending}
      className="flex items-center gap-2"
    >
      {createPost.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
      {createPost.isPending ? 'Creating...' : 'Create Post'}
    </button>
  )
}
```

### Error Display

```tsx
import { useCreatePost } from '~/mutations/post.mutations'
import { Alert, AlertDescription } from '~/components/ui/alert'

export function CreatePostForm() {
  const createPost = useCreatePost()

  return (
    <div>
      {createPost.error && (
        <Alert variant="destructive">
          <AlertDescription>{createPost.error.message}</AlertDescription>
        </Alert>
      )}
      <form onSubmit={(e) => {
        e.preventDefault()
        createPost.mutate(/* data */)
      }}>
        {/* form fields */}
      </form>
    </div>
  )
}
```

### Success Feedback

```tsx
import { useCreatePost } from '~/mutations/post.mutations'
import { useEffect } from 'react'
import { toast } from '~/components/ui/use-toast'

export function CreatePostForm() {
  const createPost = useCreatePost()

  useEffect(() => {
    if (createPost.isSuccess) {
      toast({ title: 'Post created successfully!' })
      // Optional: redirect or reset form
    }
  }, [createPost.isSuccess])

  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      createPost.mutate(/* data */)
    }}>
      {/* form fields */}
    </form>
  )
}
```

## Pattern 9: Mutation Context

Pass additional data through mutation lifecycle:

```typescript
export function useUpdatePostStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updatePostStatus,
    onMutate: async ({ postId, newStatus }) => {
      await queryClient.cancelQueries({
        queryKey: queryKeys.posts.detail(postId),
      })

      const previousPost = queryClient.getQueryData<Post>(
        queryKeys.posts.detail(postId)
      )

      // Optimistically update
      queryClient.setQueryData<Post>(
        queryKeys.posts.detail(postId),
        (old) => old ? { ...old, status: newStatus } : old
      )

      // Return context with additional data
      return {
        previousPost,
        postId,
        timestamp: Date.now(),
      }
    },
    onError: (err, variables, context) => {
      // Access context data
      console.log('Mutation failed at', context?.timestamp)

      if (context?.previousPost) {
        queryClient.setQueryData<Post>(
          queryKeys.posts.detail(context.postId),
          context.previousPost
        )
      }
    },
    onSuccess: (data, variables, context) => {
      // Access context data
      console.log('Mutation took', Date.now() - (context?.timestamp || 0), 'ms')
    },
  })
}
```

## Pattern 10: Debounced Mutations

Debounce frequent mutations (e.g., auto-save):

```tsx
import { useMutation } from '@tanstack/react-query'
import { useDebounce } from '~/hooks/use-debounce'
import { useEffect, useState } from 'react'
import { updatePost } from '~/api/posts'

export function AutoSaveEditor({ postId }: { postId: string }) {
  const [content, setContent] = useState('')
  const debouncedContent = useDebounce(content, 1000)

  const savePost = useMutation({
    mutationFn: (content: string) => updatePost({ id: postId, content }),
  })

  useEffect(() => {
    if (debouncedContent) {
      savePost.mutate(debouncedContent)
    }
  }, [debouncedContent])

  return (
    <div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="w-full"
      />
      {savePost.isPending && <span>Saving...</span>}
      {savePost.isSuccess && <span>Saved!</span>}
    </div>
  )
}
```

## Best Practices

### DO

✅ Always handle errors appropriately
✅ Use optimistic updates for better UX
✅ Invalidate related queries after mutations
✅ Provide loading states for pending mutations
✅ Use `mutateAsync` for sequential mutations
✅ Implement rollback on error
✅ Show success feedback to users
✅ Disable submit buttons during mutations

### DON'T

❌ Forget to invalidate queries after mutations
❌ Ignore error handling
❌ Over-invalidate (too broad)
❌ Mutate without user feedback
❌ Allow multiple simultaneous submissions
❌ Skip optimistic updates for instant actions
❌ Forget to handle network failures
❌ Mutate without confirmation for destructive actions

## Common Patterns Summary

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| Basic Mutation | Simple CRUD | `mutationFn` + callbacks |
| Cache Invalidation | Keep data fresh | `invalidateQueries` |
| Optimistic Updates | Instant feedback | Update before server |
| Sequential Mutations | Dependent operations | `mutateAsync` chaining |
| Parallel Mutations | Independent operations | `Promise.all` |
| Form Integration | Form submission | React Hook Form |
| Debounced Mutations | Auto-save | Debounce + useEffect |
| Global Defaults | Consistent behavior | QueryClient config |

## Mutation Lifecycle

```
┌─────────────┐
│   mutate()  │
└──────┬──────┘
       │
       v
┌─────────────┐
│  onMutate   │ ← Optimistic update
└──────┬──────┘
       │
       v
┌─────────────┐
│ mutationFn  │ ← API call
└──────┬──────┘
       │
       ├─ Success ──> onSuccess ──> onSettled
       │
       └─ Error ────> onError ────> onSettled
```

## Project Structure

```
src/
├── mutations/              # Mutation definitions
│   ├── user.mutations.ts
│   ├── post.mutations.ts
│   └── comment.mutations.ts
├── lib/
│   ├── query-client.ts    # Global mutation config
│   └── query-keys.ts      # For invalidation
└── api/                   # API functions
    ├── users.ts
    ├── posts.ts
    └── comments.ts
```

## Next Steps

After mastering mutations:
- Set up API layer with error handling (see `tanstack-client-api-layer` skill)
- Add authentication flows (see `tanstack-client-auth` skill)
- Build data tables with mutations (see `tanstack-shadcn-data-tables` skill)
- Implement form validation (see `tanstack-shadcn-forms` skill)

## Resources

- [TanStack Query Mutations](https://tanstack.com/query/latest/docs/react/guides/mutations)
- [Optimistic Updates](https://tanstack.com/query/latest/docs/react/guides/optimistic-updates)
- [Invalidation from Mutations](https://tanstack.com/query/latest/docs/react/guides/invalidations-from-mutations)
- [React Hook Form Integration](https://react-hook-form.com/get-started)

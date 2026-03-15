import { createFileRoute, redirect } from '@tanstack/react-router'
import { useItems } from '@/hooks/useItems'
import { isAuthenticated } from '@/lib/auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CreateItemDialog } from '@/components/CreateItemDialog'
import { EditItemDialog } from '@/components/EditItemDialog'
import { DeleteItemDialog } from '@/components/DeleteItemDialog'
import { Pencil, Trash2, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useState, useCallback } from 'react'
import { useDebounce } from '@/hooks/useDebounce'

function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'Invalid Date'
  return date.toLocaleDateString()
}

export const Route = createFileRoute('/items')({
  beforeLoad: () => {
    if (!isAuthenticated()) {
      throw redirect({ to: '/login', search: { redirect: '/items' } })
    }
  },
  component: Items,
})

function Items() {
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const pageSize = 9
  const debouncedSearchTerm = useDebounce(searchInput, 300)

  const { data, isLoading, isError, error } = useItems({
    page,
    size: pageSize,
    name: debouncedSearchTerm || undefined,
  })

  const handleClearSearch = useCallback(() => {
    setSearchInput('')
    setPage(1)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background pt-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold mb-6 text-foreground">Items</h1>
          <p className="text-muted-foreground">Loading items...</p>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-background pt-20">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold mb-6 text-foreground">Items</h1>
          <div className="bg-destructive/10 text-destructive p-4 rounded-md border border-destructive/20">
            <p className="font-semibold">Error loading items</p>
            <p className="text-sm">{error instanceof Error ? error.message : 'An unknown error occurred'}</p>
          </div>
        </div>
      </div>
    )
  }

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = data?.pages ?? 1
  const hasNextPage = page < totalPages
  const hasPrevPage = page > 1

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div role="status" aria-live="polite" className="sr-only">
          {`Showing ${items.length} of ${total} items`}
        </div>

        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Items</h1>
            <p className="text-muted-foreground mt-1">
              {total === 0 ? 'No items found' : `${total} ${total === 1 ? 'item' : 'items'} total`}
            </p>
          </div>
          <CreateItemDialog />
        </div>

        <div className="flex gap-2 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search items by name..."
              value={searchInput}
              onChange={(e) => {
              setSearchInput(e.target.value)
              setPage(1)
            }}
              className="pl-9"
            />
          </div>
          {searchInput && (
            <Button onClick={handleClearSearch} variant="outline">
              Clear
            </Button>
          )}
        </div>

        {items.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-foreground">No items yet</CardTitle>
              <CardDescription>Get started by creating your first item.</CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <Card key={item.id} data-testid="item-card">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-foreground">{item.name}</CardTitle>
                      {item.description && (
                        <CardDescription>{item.description}</CardDescription>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <EditItemDialog item={item}>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          aria-label={`Edit ${item.name}`}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                      </EditItemDialog>
                      <DeleteItemDialog item={item}>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          aria-label={`Delete ${item.name}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </DeleteItemDialog>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground">
                    <p>Created: {formatDate(item.created_at)}</p>
                    {item.updated_at !== item.created_at && (
                      <p>Updated: {formatDate(item.updated_at)}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {total > 0 && totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6" role="navigation" aria-label="Pagination">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={!hasPrevPage}
              aria-label="Go to previous page"
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <div className="flex items-center gap-1">
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasNextPage}
              aria-label="Go to next page"
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

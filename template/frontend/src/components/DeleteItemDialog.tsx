import { useState } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { useDeleteItem } from '@/hooks/useItems'
import type { Item } from '@/types/item'
import { handleApiError } from '@/lib/error-handler'

interface DeleteItemDialogProps {
  item: Item
  children?: React.ReactNode
}

export function DeleteItemDialog({ item, children }: DeleteItemDialogProps) {
  const [open, setOpen] = useState(false)
  const deleteItem = useDeleteItem(item.id)

  const handleDelete = async () => {
    try {
      await deleteItem.mutateAsync()
      setOpen(false)
    } catch (error) {
      handleApiError(error, 'Failed to delete item')
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        {children || <Button variant="destructive">Delete</Button>}
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Item</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete "{item.name}"? This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteItem.isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault()
              handleDelete()
            }}
            disabled={deleteItem.isPending}
            variant="destructive"
          >
            {deleteItem.isPending ? 'Deleting...' : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

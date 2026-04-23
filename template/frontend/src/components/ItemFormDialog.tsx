import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import type { Item } from '@/types/item'
import { toastApiError } from '@/lib/error-handler'
import { itemSchema, type ItemFormData } from '@/lib/item-schemas'

type ItemFormDialogProps =
  | { mode: 'create'; trigger: React.ReactNode; onSubmit: (data: ItemFormData) => Promise<void>; isPending: boolean; item?: never }
  | { mode: 'edit'; item: Item; trigger: React.ReactNode; onSubmit: (data: ItemFormData) => Promise<void>; isPending: boolean }

export function ItemFormDialog({
  mode,
  item,
  trigger,
  onSubmit,
  isPending,
}: ItemFormDialogProps) {
  const [open, setOpen] = useState(false)

  const form = useForm<ItemFormData>({
    resolver: zodResolver(itemSchema),
    defaultValues: {
      name: item?.name || '',
      description: item?.description || '',
    },
  })

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen)
    if (!newOpen) {
      form.reset()
    } else if (mode === 'edit' && item) {
      form.reset({
        name: item.name,
        description: item.description || '',
      })
    }
  }

  const handleSubmit = async (data: ItemFormData) => {
    try {
      await onSubmit(data)
      setOpen(false)
    } catch (error) {
      toastApiError(
        error,
        mode === 'create' ? 'Failed to create item' : 'Failed to update item'
      )
    }
  }

  const dialogContent = {
    create: {
      title: 'Create New Item',
      description: 'Add a new item to your collection. Fill in the details below.',
      submitText: 'Create',
      submittingText: 'Creating...',
    },
    edit: {
      title: 'Edit Item',
      description: 'Update the details of your item below.',
      submitText: 'Update',
      submittingText: 'Updating...',
    },
  }

  const content = dialogContent[mode]

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{content.title}</DialogTitle>
          <DialogDescription>{content.description}</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form method="post" action="#" onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter item name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (Optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Enter item description"
                      {...field}
                      rows={3}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => handleOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? content.submittingText : content.submitText}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

import React from 'react'
import { useCreateItem } from '@/hooks/useItems'
import { ItemFormDialog } from './ItemFormDialog'
import { itemFormToPayload, type ItemFormData } from '@/lib/schemas'

interface CreateItemDialogProps {
  trigger: React.ReactNode
}

export function CreateItemDialog({ trigger }: CreateItemDialogProps) {
  const createItem = useCreateItem()

  const handleSubmit = (data: ItemFormData) =>
    createItem.mutateAsync(itemFormToPayload(data))

  return (
    <ItemFormDialog
      mode="create"
      trigger={trigger}
      onSubmit={handleSubmit}
      isPending={createItem.isPending}
    />
  )
}

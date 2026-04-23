import { useUpdateItem } from '@/hooks/useItems'
import type { Item } from '@/types/item'
import { ItemFormDialog } from './ItemFormDialog'
import { itemFormToPayload, type ItemFormData } from '@/lib/item-schemas'

interface EditItemDialogProps {
  item: Item
  trigger: React.ReactNode
}

export function EditItemDialog({ item, trigger }: EditItemDialogProps) {
  const updateItem = useUpdateItem(item.id)

  const handleSubmit = async (data: ItemFormData): Promise<void> => {
    await updateItem.mutateAsync(itemFormToPayload(data))
  }

  return (
    <ItemFormDialog
      mode="edit"
      item={item}
      trigger={trigger}
      onSubmit={handleSubmit}
      isPending={updateItem.isPending}
    />
  )
}

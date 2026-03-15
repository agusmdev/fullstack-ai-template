import { useUpdateItem, type UpdateItemData } from '@/hooks/useItems'
import type { Item } from '@/types/item'
import { ItemFormDialog } from './ItemFormDialog'
import type { ItemFormData } from '@/lib/schemas'

interface EditItemDialogProps {
  item: Item
  trigger: React.ReactNode
}

export function EditItemDialog({ item, trigger }: EditItemDialogProps) {
  const updateItem = useUpdateItem(item.id)

  const handleSubmit = async (data: ItemFormData) => {
    const itemData: UpdateItemData = {
      name: data.name,
      description: data.description || undefined,
    }
    await updateItem.mutateAsync(itemData)
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

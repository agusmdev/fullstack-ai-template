import { Button } from '@/components/ui/button'
import { useCreateItem, type CreateItemData } from '@/hooks/useItems'
import { ItemFormDialog } from './ItemFormDialog'
import type { ItemFormData } from '@/lib/schemas'

export function CreateItemDialog() {
  const createItem = useCreateItem()

  const handleSubmit = async (data: ItemFormData) => {
    const itemData: CreateItemData = {
      name: data.name,
      description: data.description || undefined,
    }
    await createItem.mutateAsync(itemData)
  }

  return (
    <ItemFormDialog
      mode="create"
      trigger={<Button>Create Item</Button>}
      onSubmit={handleSubmit}
      isPending={createItem.isPending}
    />
  )
}

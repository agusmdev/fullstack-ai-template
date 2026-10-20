import { type Control, type FieldPath, type FieldValues } from 'react-hook-form'
import { FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'

interface AuthFieldProps<T extends FieldValues> {
  control: Control<T>
  name: FieldPath<T>
  disabled: boolean
}

export function EmailField<T extends FieldValues>({ control, name, disabled }: AuthFieldProps<T>) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel className="text-muted-foreground">Email</FormLabel>
          <FormControl>
            <Input type="email" placeholder="john@example.com" {...field} disabled={disabled} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

interface PasswordFieldProps<T extends FieldValues> extends AuthFieldProps<T> {
  label?: string
}

export function PasswordField<T extends FieldValues>({
  control,
  name,
  disabled,
  label = 'Password',
}: PasswordFieldProps<T>) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel className="text-muted-foreground">{label}</FormLabel>
          <FormControl>
            <Input type="password" placeholder="••••••••" {...field} disabled={disabled} />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  )
}

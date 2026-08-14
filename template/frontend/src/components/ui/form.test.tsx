import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from './form'

interface Values {
  name: string
}

function Harness() {
  const form = useForm<Values>({ defaultValues: { name: '' } })
  return (
    <Form {...form}>
      <FormField
        control={form.control}
        name="name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <input {...field} />
            </FormControl>
            <FormDescription>Your full name</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </Form>
  )
}

describe('Form primitives', () => {
  it('renders the label, control, and description', () => {
    render(<Harness />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Your full name')).toBeInTheDocument()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('FormLabel renders a label element', () => {
    render(<Harness />)
    expect(screen.getByText('Name').tagName).toBe('LABEL')
  })

  it('shows a validation message when the field has an error', async () => {
    function ErrorHarness() {
      const form = useForm<Values>({ defaultValues: { name: '' } })
      useEffect(() => {
        form.setError('name', { type: 'required', message: 'Name is required' })
      }, [form])
      return (
        <Form {...form}>
          <FormField
            control={form.control}
            name="name"
            render={() => (
              <FormItem>
                <FormMessage />
              </FormItem>
            )}
          />
        </Form>
      )
    }
    render(<ErrorHarness />)
    expect(await screen.findByText('Name is required')).toBeInTheDocument()
  })
})

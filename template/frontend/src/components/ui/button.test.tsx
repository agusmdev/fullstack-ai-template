import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Button, buttonVariants } from './button'

describe('Button', () => {
  it('renders its children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('applies the default variant and size classes', () => {
    render(<Button>Default</Button>)
    const el = screen.getByRole('button', { name: 'Default' })
    expect(el.className).toContain('bg-primary')
    expect(el.className).toContain('h-9')
  })

  it('applies the destructive + sm variant classes', () => {
    render(<Button variant="destructive" size="sm">Destructive</Button>)
    const el = screen.getByRole('button', { name: 'Destructive' })
    expect(el.className).toContain('bg-destructive')
    expect(el.className).toContain('h-8')
  })

  it('forwards native button attributes and the onClick handler', () => {
    const onClick = vi.fn()
    render(
      <Button onClick={onClick} data-testid="b" aria-label="go">
        go
      </Button>,
    )
    const el = screen.getByTestId('b')
    expect(el).not.toBeDisabled()
    fireEvent.click(el)
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('can be disabled (preventing interaction)', () => {
    render(<Button disabled>locked</Button>)
    expect(screen.getByRole('button', { name: 'locked' })).toBeDisabled()
  })

  it('buttonVariants returns a non-empty class string for the default variant', () => {
    expect(buttonVariants()).toContain('inline-flex')
  })
})

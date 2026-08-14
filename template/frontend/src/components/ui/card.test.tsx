import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from './card'

describe('Card components', () => {
  it('composes a full card with all subcomponents', () => {
    render(
      <Card data-testid="card">
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Body</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>,
    )

    expect(screen.getByTestId('card')).toBeInTheDocument()
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Body')).toBeInTheDocument()
    expect(screen.getByText('Footer')).toBeInTheDocument()
  })

  it('Card renders a div with the card border class', () => {
    render(<Card>only</Card>)
    expect(screen.getByText('only').className).toContain('rounded-xl')
  })

  it('CardTitle renders a div (not a heading) with semibold text', () => {
    render(<CardTitle>T</CardTitle>)
    const el = screen.getByText('T')
    expect(el.tagName).toBe('DIV')
    expect(el.className).toContain('font-semibold')
  })
})
